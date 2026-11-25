from uuid import UUID

from inventory.repository import InventoryRepository
from inventory.schemas import (
    AdjustmentCreate,
    BatchCreate,
    BatchStatusUpdate,
    ReservationCreate,
    StockItemCreate,
    WarehouseCreate,
)


class InventoryService:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository

    def list_warehouses(self): return self.repository.list_warehouses()
    def create_warehouse(self, payload: WarehouseCreate): return self.repository.create_warehouse(payload)
    def list_stock(self, sku: str | None = None): return self.repository.list_stock(sku)
    def create_stock_item(self, payload: StockItemCreate): return self.repository.create_stock_item(payload)
    def adjust(self, stock_item_id: UUID, payload: AdjustmentCreate, actor: str): return self.repository.adjust(stock_item_id, payload, actor)
    def movements(self, stock_item_id: UUID, limit: int): return self.repository.movements(stock_item_id, limit)
    def batches(self, stock_item_id: UUID): return self.repository.list_batches(stock_item_id)
    def create_batch(self, stock_item_id: UUID, payload: BatchCreate, actor: str): return self.repository.create_batch(stock_item_id, payload, actor)
    def update_batch_status(self, stock_item_id: UUID, batch_id: UUID, payload: BatchStatusUpdate, actor: str): return self.repository.update_batch_status(stock_item_id, batch_id, payload, actor)
    def reserve(self, payload: ReservationCreate, actor: str): return self.repository.reserve(payload, actor)
    def get_reservation(self, reservation_id: UUID): return self.repository.get_reservation(reservation_id)
    def release(self, reservation_id: UUID, actor: str): return self.repository.transition_reservation(reservation_id, "RELEASED", actor)
    def commit(self, reservation_id: UUID, actor: str): return self.repository.transition_reservation(reservation_id, "COMMITTED", actor)
