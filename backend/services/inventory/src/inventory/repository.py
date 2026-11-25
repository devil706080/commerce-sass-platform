from datetime import date
from uuid import UUID

from psycopg.rows import dict_row

from inventory.config import Settings
from inventory.database import connect, identifier
from inventory.errors import InventoryConflict, InventoryNotFound
from inventory.schemas import (
    AdjustmentCreate,
    BatchCreate,
    BatchStatusUpdate,
    ReservationCreate,
    StockItemCreate,
    WarehouseCreate,
)


class InventoryRepository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.schema = identifier(settings.schema_name)

    def list_warehouses(self):
        with connect(self.settings) as db:
            return db.execute(f"SELECT id,code,name,active FROM {self.schema}.warehouses ORDER BY name", row_factory=dict_row).fetchall()

    def create_warehouse(self, payload: WarehouseCreate):
        with connect(self.settings) as db:
            try:
                row = db.execute(f"INSERT INTO {self.schema}.warehouses(code,name) VALUES (%s,%s) RETURNING id,code,name,active", (payload.code, payload.name), row_factory=dict_row).fetchone()
                db.commit(); return row
            except Exception as exc:
                db.rollback(); raise InventoryConflict("Warehouse code already exists") from exc

    def list_stock(self, sku: str | None = None):
        where, params = (" WHERE sku=%s", (sku,)) if sku else (" WHERE product_id IS NOT NULL AND warehouse_id IS NOT NULL", ())
        with connect(self.settings) as db:
            return db.execute(
                f"SELECT s.id,s.product_id,s.variant_id,s.sku,s.warehouse_id,s.on_hand,s.reserved,s.damaged,"
                f"GREATEST(0,s.on_hand-s.reserved-s.damaged-COALESCE((SELECT sum(b.on_hand-b.reserved) "
                f"FROM {self.schema}.batches b WHERE b.stock_item_id=s.id AND "
                "(b.status<>'AVAILABLE' OR (b.expires_on IS NOT NULL AND b.expires_on<current_date))),0)) "
                "AS available,s.low_stock_threshold,s.version,s.updated_at "
                f"FROM {self.schema}.stock_items s{where} ORDER BY s.sku",
                params,
                row_factory=dict_row,
            ).fetchall()

    def create_stock_item(self, payload: StockItemCreate):
        with connect(self.settings) as db:
            try:
                row = db.execute(f"INSERT INTO {self.schema}.stock_items(product_id,variant_id,sku,warehouse_id,low_stock_threshold) VALUES (%s,%s,%s,%s,%s) RETURNING id,product_id,variant_id,sku,warehouse_id,on_hand,reserved,damaged,(on_hand-reserved-damaged) AS available,low_stock_threshold,version,updated_at", (payload.product_id, payload.variant_id, payload.sku, payload.warehouse_id, payload.low_stock_threshold), row_factory=dict_row).fetchone()
                db.commit(); return row
            except Exception as exc:
                db.rollback(); raise InventoryConflict("SKU already exists or warehouse is invalid") from exc

    def adjust(self, stock_item_id: UUID, payload: AdjustmentCreate, actor: str):
        with connect(self.settings) as db:
            existing = db.execute(f"SELECT id,stock_item_id,movement_type,quantity_delta,reason,source_reference,actor_subject,created_at FROM {self.schema}.stock_movements WHERE idempotency_key=%s", (payload.idempotency_key,), row_factory=dict_row).fetchone()
            if existing: return existing
            item = db.execute(f"SELECT on_hand,reserved,damaged FROM {self.schema}.stock_items WHERE id=%s FOR UPDATE", (stock_item_id,), row_factory=dict_row).fetchone()
            if not item: raise InventoryNotFound("Stock item not found")
            on_hand = item["on_hand"] + (payload.quantity_delta if payload.bucket == "SELLABLE" else 0)
            damaged = item["damaged"] + (payload.quantity_delta if payload.bucket == "DAMAGED" else 0)
            if on_hand < 0 or damaged < 0 or on_hand - item["reserved"] - damaged < 0:
                raise InventoryConflict("Adjustment would make sellable inventory negative")
            db.execute(f"UPDATE {self.schema}.stock_items SET on_hand=%s,damaged=%s,version=version+1,updated_at=now() WHERE id=%s", (on_hand, damaged, stock_item_id))
            row = db.execute(f"INSERT INTO {self.schema}.stock_movements(stock_item_id,movement_type,quantity_delta,reason,source_reference,actor_subject,idempotency_key) VALUES (%s,'ADJUSTMENT',%s,%s,%s,%s,%s) RETURNING id,stock_item_id,movement_type,quantity_delta,reason,source_reference,actor_subject,created_at", (stock_item_id, payload.quantity_delta, payload.reason, payload.source_reference, actor, payload.idempotency_key), row_factory=dict_row).fetchone()
            db.commit(); return row

    def movements(self, stock_item_id: UUID, limit: int):
        with connect(self.settings) as db:
            return db.execute(f"SELECT id,stock_item_id,movement_type,quantity_delta,reason,source_reference,actor_subject,created_at FROM {self.schema}.stock_movements WHERE stock_item_id=%s ORDER BY created_at DESC LIMIT %s", (stock_item_id, limit), row_factory=dict_row).fetchall()

    def list_batches(self, stock_item_id: UUID):
        with connect(self.settings) as db:
            return db.execute(
                f"SELECT id,stock_item_id,lot_number,manufactured_on,expires_on,status,on_hand,reserved,"
                f"(on_hand-reserved) AS available,(expires_on IS NOT NULL AND expires_on<current_date) AS expired,"
                f"created_at,updated_at FROM {self.schema}.batches WHERE stock_item_id=%s "
                "ORDER BY expires_on ASC NULLS LAST,created_at,id",
                (stock_item_id,),
                row_factory=dict_row,
            ).fetchall()

    def create_batch(self, stock_item_id: UUID, payload: BatchCreate, actor: str):
        with connect(self.settings) as db:
            existing = db.execute(
                f"SELECT id FROM {self.schema}.batches WHERE receipt_idempotency_key=%s",
                (payload.idempotency_key,),
            ).fetchone()
            if existing:
                db.commit()
                return self._get_batch(existing[0])
            item = db.execute(
                f"SELECT id FROM {self.schema}.stock_items WHERE id=%s FOR UPDATE",
                (stock_item_id,),
            ).fetchone()
            if not item:
                raise InventoryNotFound("Stock item not found")
            try:
                batch_id = db.execute(
                    f"INSERT INTO {self.schema}.batches"
                    "(stock_item_id,lot_number,manufactured_on,expires_on,on_hand,receipt_idempotency_key) "
                    "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                    (
                        stock_item_id,
                        payload.lot_number,
                        payload.manufactured_on,
                        payload.expires_on,
                        payload.quantity,
                        payload.idempotency_key,
                    ),
                ).fetchone()[0]
                db.execute(
                    f"UPDATE {self.schema}.stock_items SET on_hand=on_hand+%s,version=version+1,"
                    "updated_at=now() WHERE id=%s",
                    (payload.quantity, stock_item_id),
                )
                db.execute(
                    f"INSERT INTO {self.schema}.stock_movements"
                    "(stock_item_id,movement_type,quantity_delta,reason,source_reference,actor_subject,idempotency_key) "
                    "VALUES (%s,'BATCH_RECEIPT',%s,%s,%s,%s,%s)",
                    (
                        stock_item_id,
                        payload.quantity,
                        f"Received batch {payload.lot_number}",
                        payload.source_reference,
                        actor,
                        payload.idempotency_key,
                    ),
                )
                db.commit()
                return self._get_batch(batch_id)
            except Exception as exc:
                db.rollback()
                raise InventoryConflict("Batch lot or idempotency key already exists") from exc

    def _get_batch(self, batch_id: UUID):
        with connect(self.settings) as db:
            batch = db.execute(
                f"SELECT id,stock_item_id,lot_number,manufactured_on,expires_on,status,on_hand,reserved,"
                f"(on_hand-reserved) AS available,(expires_on IS NOT NULL AND expires_on<current_date) AS expired,"
                f"created_at,updated_at FROM {self.schema}.batches WHERE id=%s",
                (batch_id,),
                row_factory=dict_row,
            ).fetchone()
            if not batch:
                raise InventoryNotFound("Batch not found")
            return batch

    def update_batch_status(
        self, stock_item_id: UUID, batch_id: UUID, payload: BatchStatusUpdate, actor: str
    ):
        with connect(self.settings) as db:
            existing = db.execute(
                f"SELECT batch_id FROM {self.schema}.batch_events WHERE idempotency_key=%s",
                (payload.idempotency_key,),
            ).fetchone()
            if existing:
                db.commit()
                return self._get_batch(existing[0])
            batch = db.execute(
                f"SELECT status,reserved FROM {self.schema}.batches "
                "WHERE id=%s AND stock_item_id=%s FOR UPDATE",
                (batch_id, stock_item_id),
            ).fetchone()
            if not batch:
                raise InventoryNotFound("Batch not found")
            previous_status, reserved = batch
            if payload.status != "AVAILABLE" and reserved:
                raise InventoryConflict("Release or commit active reservations before blocking this batch")
            db.execute(
                f"UPDATE {self.schema}.batches SET status=%s,updated_at=now() WHERE id=%s",
                (payload.status, batch_id),
            )
            db.execute(
                f"INSERT INTO {self.schema}.batch_events"
                "(batch_id,previous_status,new_status,reason,actor_subject,idempotency_key) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    batch_id,
                    previous_status,
                    payload.status,
                    payload.reason,
                    actor,
                    payload.idempotency_key,
                ),
            )
            db.commit()
            return self._get_batch(batch_id)

    def _expire(self, db) -> None:
        allocations = db.execute(
            f"SELECT a.batch_id,a.quantity FROM {self.schema}.reservation_allocations a "
            f"JOIN {self.schema}.reservations r ON r.id=a.reservation_id "
            "WHERE r.status='ACTIVE' AND r.expires_at<=now() ORDER BY a.batch_id FOR UPDATE OF r,a"
        ).fetchall()
        for batch_id, quantity in allocations:
            db.execute(
                f"UPDATE {self.schema}.batches SET reserved=reserved-%s,updated_at=now() WHERE id=%s",
                (quantity, batch_id),
            )
        lines = db.execute(f"SELECT rl.stock_item_id,rl.quantity FROM {self.schema}.reservation_lines rl JOIN {self.schema}.reservations r ON r.id=rl.reservation_id WHERE r.status='ACTIVE' AND r.expires_at<=now() ORDER BY rl.stock_item_id FOR UPDATE OF r,rl").fetchall()
        for stock_item_id, quantity in lines:
            db.execute(f"UPDATE {self.schema}.stock_items SET reserved=reserved-%s,version=version+1,updated_at=now() WHERE id=%s", (quantity, stock_item_id))
        db.execute(f"UPDATE {self.schema}.reservations SET status='EXPIRED',updated_at=now() WHERE status='ACTIVE' AND expires_at<=now()")

    def reserve(self, payload: ReservationCreate, actor: str):
        with connect(self.settings) as db:
            self._expire(db)
            existing = db.execute(f"SELECT id FROM {self.schema}.reservations WHERE idempotency_key=%s", (payload.idempotency_key,)).fetchone()
            if existing: db.commit(); return self.get_reservation(existing[0])
            reservation_id = db.execute(f"INSERT INTO {self.schema}.reservations(idempotency_key,source_reference,status,expires_at,actor_subject) VALUES (%s,%s,'ACTIVE',now()+(%s*interval '1 second'),%s) RETURNING id", (payload.idempotency_key, payload.source_reference, payload.ttl_seconds, actor)).fetchone()[0]
            for line in sorted(payload.lines, key=lambda item: item.sku):
                item = db.execute(f"SELECT id,on_hand,reserved,damaged FROM {self.schema}.stock_items WHERE sku=%s FOR UPDATE", (line.sku,)).fetchone()
                if not item: raise InventoryNotFound(f"Inventory SKU {line.sku} not found")
                batches = db.execute(
                    f"SELECT id,on_hand,reserved,status,expires_on FROM {self.schema}.batches "
                    "WHERE stock_item_id=%s ORDER BY expires_on ASC NULLS LAST,created_at,id FOR UPDATE",
                    (item[0],),
                ).fetchall()
                batch_total = sum(batch[1] for batch in batches)
                batch_reserved = sum(batch[2] for batch in batches)
                unbatched_reserved = max(0, item[2] - batch_reserved)
                unbatched_available = max(
                    0, item[1] - batch_total - unbatched_reserved - item[3]
                )
                eligible = [
                    batch
                    for batch in batches
                    if batch[3] == "AVAILABLE"
                    and (batch[4] is None or batch[4] >= date.today())
                ]
                batch_available = sum(batch[1] - batch[2] for batch in eligible)
                if unbatched_available + batch_available < line.quantity:
                    raise InventoryConflict(f"Insufficient sellable stock for SKU {line.sku}")
                db.execute(f"UPDATE {self.schema}.stock_items SET reserved=reserved+%s,version=version+1,updated_at=now() WHERE id=%s", (line.quantity, item[0]))
                db.execute(f"INSERT INTO {self.schema}.reservation_lines(reservation_id,stock_item_id,quantity) VALUES (%s,%s,%s)", (reservation_id, item[0], line.quantity))
                remaining = line.quantity
                for batch in eligible:
                    allocated = min(remaining, batch[1] - batch[2])
                    if allocated <= 0:
                        continue
                    db.execute(
                        f"UPDATE {self.schema}.batches SET reserved=reserved+%s,updated_at=now() WHERE id=%s",
                        (allocated, batch[0]),
                    )
                    db.execute(
                        f"INSERT INTO {self.schema}.reservation_allocations"
                        "(reservation_id,stock_item_id,batch_id,quantity) VALUES (%s,%s,%s,%s)",
                        (reservation_id, item[0], batch[0], allocated),
                    )
                    remaining -= allocated
                    if remaining == 0:
                        break
            db.commit(); return self.get_reservation(reservation_id)

    def get_reservation(self, reservation_id: UUID):
        with connect(self.settings) as db:
            reservation = db.execute(f"SELECT id,idempotency_key,source_reference,status,expires_at FROM {self.schema}.reservations WHERE id=%s", (reservation_id,), row_factory=dict_row).fetchone()
            if not reservation: raise InventoryNotFound("Reservation not found")
            reservation["lines"] = db.execute(f"SELECT rl.stock_item_id,s.sku,rl.quantity FROM {self.schema}.reservation_lines rl JOIN {self.schema}.stock_items s ON s.id=rl.stock_item_id WHERE rl.reservation_id=%s ORDER BY s.sku", (reservation_id,), row_factory=dict_row).fetchall()
            reservation["allocations"] = db.execute(
                f"SELECT a.stock_item_id,a.batch_id,b.lot_number,b.expires_on,a.quantity "
                f"FROM {self.schema}.reservation_allocations a JOIN {self.schema}.batches b ON b.id=a.batch_id "
                "WHERE a.reservation_id=%s ORDER BY b.expires_on ASC NULLS LAST,b.created_at,b.id",
                (reservation_id,),
                row_factory=dict_row,
            ).fetchall()
            return reservation

    def transition_reservation(self, reservation_id: UUID, target: str, actor: str):
        with connect(self.settings) as db:
            self._expire(db)
            reservation = db.execute(f"SELECT status FROM {self.schema}.reservations WHERE id=%s FOR UPDATE", (reservation_id,)).fetchone()
            if not reservation: raise InventoryNotFound("Reservation not found")
            if reservation[0] == target: db.commit(); return self.get_reservation(reservation_id)
            if reservation[0] != "ACTIVE": raise InventoryConflict(f"Reservation is already {reservation[0].lower()}")
            lines = db.execute(f"SELECT stock_item_id,quantity FROM {self.schema}.reservation_lines WHERE reservation_id=%s ORDER BY stock_item_id FOR UPDATE", (reservation_id,)).fetchall()
            allocations = db.execute(
                f"SELECT batch_id,quantity FROM {self.schema}.reservation_allocations "
                "WHERE reservation_id=%s ORDER BY batch_id FOR UPDATE",
                (reservation_id,),
            ).fetchall()
            for batch_id, quantity in allocations:
                if target == "COMMITTED":
                    db.execute(
                        f"UPDATE {self.schema}.batches SET on_hand=on_hand-%s,reserved=reserved-%s,"
                        "updated_at=now() WHERE id=%s",
                        (quantity, quantity, batch_id),
                    )
                else:
                    db.execute(
                        f"UPDATE {self.schema}.batches SET reserved=reserved-%s,updated_at=now() WHERE id=%s",
                        (quantity, batch_id),
                    )
            for stock_item_id, quantity in lines:
                if target == "COMMITTED":
                    db.execute(f"UPDATE {self.schema}.stock_items SET on_hand=on_hand-%s,reserved=reserved-%s,version=version+1,updated_at=now() WHERE id=%s", (quantity, quantity, stock_item_id))
                    db.execute(f"INSERT INTO {self.schema}.stock_movements(stock_item_id,movement_type,quantity_delta,reason,source_reference,actor_subject,idempotency_key) VALUES (%s,'RESERVATION_COMMIT',%s,'Committed reservation',%s,%s,%s)", (stock_item_id, -quantity, str(reservation_id), actor, f"commit:{reservation_id}:{stock_item_id}"))
                else:
                    db.execute(f"UPDATE {self.schema}.stock_items SET reserved=reserved-%s,version=version+1,updated_at=now() WHERE id=%s", (quantity, stock_item_id))
            db.execute(f"UPDATE {self.schema}.reservations SET status=%s,updated_at=now() WHERE id=%s", (target, reservation_id))
            db.commit(); return self.get_reservation(reservation_id)
