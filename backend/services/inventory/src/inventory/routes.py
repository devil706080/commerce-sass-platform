from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from inventory.auth import InventoryIdentity
from inventory.errors import InventoryConflict, InventoryNotFound
from inventory.repository import InventoryRepository
from inventory.schemas import (
    AdjustmentCreate,
    Batch,
    BatchCreate,
    BatchStatusUpdate,
    InventoryAlert,
    InventoryDashboardSummary,
    Movement,
    Reservation,
    ReservationCreate,
    StockItem,
    StockItemCreate,
    StockReceiptCreate,
    Warehouse,
    WarehouseCreate,
)
from inventory.service import InventoryService
from inventory.tenant_context import inventory_context

router = APIRouter(prefix="/api/v1")


def service(request: Request, _identity: InventoryIdentity = Depends(inventory_context)) -> InventoryService:
    return InventoryService(InventoryRepository(request.state.tenant_settings))


def translate(operation):
    try: return operation()
    except InventoryNotFound as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InventoryConflict as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/warehouses", response_model=list[Warehouse])
def warehouses(inventory: InventoryService = Depends(service)): return inventory.list_warehouses()


@router.post("/warehouses", response_model=Warehouse, status_code=201)
def create_warehouse(payload: WarehouseCreate, inventory: InventoryService = Depends(service)): return translate(lambda: inventory.create_warehouse(payload))


@router.get("/stock-items", response_model=list[StockItem])
def stock_items(sku: str | None = Query(default=None, max_length=100), inventory: InventoryService = Depends(service)): return inventory.list_stock(sku)


@router.get("/availability/{sku}", response_model=list[StockItem])
def availability(sku: str, inventory: InventoryService = Depends(service)): return inventory.list_stock(sku)


@router.post("/stock-items", response_model=StockItem, status_code=201)
def create_stock_item(payload: StockItemCreate, inventory: InventoryService = Depends(service)): return translate(lambda: inventory.create_stock_item(payload))


@router.post("/stock-items/{stock_item_id}/adjustments", response_model=Movement, status_code=201)
def adjust(stock_item_id: UUID, payload: AdjustmentCreate, identity: InventoryIdentity = Depends(inventory_context), inventory: InventoryService = Depends(service)): return translate(lambda: inventory.adjust(stock_item_id, payload, identity.subject))


@router.get("/stock-items/{stock_item_id}/movements", response_model=list[Movement])
def movements(stock_item_id: UUID, limit: int = Query(50, ge=1, le=200), inventory: InventoryService = Depends(service)): return inventory.movements(stock_item_id, limit)


@router.post("/stock-items/{stock_item_id}/receipts", response_model=Movement, status_code=201)
def receive_simple_stock(
    stock_item_id: UUID,
    payload: StockReceiptCreate,
    identity: InventoryIdentity = Depends(inventory_context),
    inventory: InventoryService = Depends(service),
):
    return translate(
        lambda: inventory.receive_simple_stock(stock_item_id, payload, identity.subject)
    )


@router.get("/stock-items/{stock_item_id}/batches", response_model=list[Batch])
def batches(stock_item_id: UUID, inventory: InventoryService = Depends(service)):
    return inventory.batches(stock_item_id)


@router.post("/stock-items/{stock_item_id}/batches", response_model=Batch, status_code=201)
def create_batch(
    stock_item_id: UUID,
    payload: BatchCreate,
    identity: InventoryIdentity = Depends(inventory_context),
    inventory: InventoryService = Depends(service),
):
    return translate(lambda: inventory.create_batch(stock_item_id, payload, identity.subject))


@router.patch("/stock-items/{stock_item_id}/batches/{batch_id}/status", response_model=Batch)
def update_batch_status(
    stock_item_id: UUID,
    batch_id: UUID,
    payload: BatchStatusUpdate,
    identity: InventoryIdentity = Depends(inventory_context),
    inventory: InventoryService = Depends(service),
):
    return translate(
        lambda: inventory.update_batch_status(stock_item_id, batch_id, payload, identity.subject)
    )


@router.get("/dashboard/summary", response_model=InventoryDashboardSummary)
def dashboard_summary(inventory: InventoryService = Depends(service)):
    return inventory.dashboard_summary()


@router.get("/alerts", response_model=list[InventoryAlert])
def alerts(
    type: str = Query(pattern="^(LOW_STOCK|OUT_OF_STOCK|EXPIRING)$"),
    limit: int = Query(default=20, ge=1, le=100),
    inventory: InventoryService = Depends(service),
):
    return inventory.alerts(type, limit)


@router.post("/reservations", response_model=Reservation, status_code=201)
def reserve(payload: ReservationCreate, identity: InventoryIdentity = Depends(inventory_context), inventory: InventoryService = Depends(service)): return translate(lambda: inventory.reserve(payload, identity.subject))


@router.get("/reservations/{reservation_id}", response_model=Reservation)
def reservation(reservation_id: UUID, inventory: InventoryService = Depends(service)): return translate(lambda: inventory.get_reservation(reservation_id))


@router.post("/reservations/{reservation_id}/release", response_model=Reservation)
def release(reservation_id: UUID, identity: InventoryIdentity = Depends(inventory_context), inventory: InventoryService = Depends(service)): return translate(lambda: inventory.release(reservation_id, identity.subject))


@router.post("/reservations/{reservation_id}/commit", response_model=Reservation)
def commit(reservation_id: UUID, identity: InventoryIdentity = Depends(inventory_context), inventory: InventoryService = Depends(service)): return translate(lambda: inventory.commit(reservation_id, identity.subject))
