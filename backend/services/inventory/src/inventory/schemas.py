from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Z0-9][A-Z0-9_-]*$")
    name: str = Field(min_length=1, max_length=160)


class Warehouse(WarehouseCreate):
    id: UUID
    active: bool


class StockItemCreate(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    sku: str = Field(min_length=1, max_length=100)
    warehouse_id: UUID
    low_stock_threshold: int = Field(default=5, ge=0)
    tracking_mode: Literal["SIMPLE", "BATCH_EXPIRY"] = "SIMPLE"


class StockItem(BaseModel):
    id: UUID
    product_id: UUID
    variant_id: UUID | None
    sku: str
    warehouse_id: UUID
    on_hand: int
    reserved: int
    damaged: int
    available: int
    low_stock_threshold: int
    tracking_mode: Literal["SIMPLE", "BATCH_EXPIRY"]
    version: int
    updated_at: datetime


class AdjustmentCreate(BaseModel):
    quantity_delta: int
    bucket: Literal["SELLABLE", "DAMAGED"] = "SELLABLE"
    reason: str = Field(min_length=3, max_length=500)
    source_reference: str | None = Field(default=None, max_length=160)
    idempotency_key: str = Field(min_length=8, max_length=160)

    @field_validator("quantity_delta")
    @classmethod
    def quantity_must_change(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Quantity adjustment cannot be zero")
        return value


class StockReceiptCreate(BaseModel):
    quantity: int = Field(gt=0, le=10_000_000)
    source_reference: str | None = Field(default=None, max_length=160)
    idempotency_key: str = Field(min_length=8, max_length=160)


class Movement(BaseModel):
    id: UUID
    stock_item_id: UUID
    movement_type: str
    quantity_delta: int
    reason: str
    source_reference: str | None
    actor_subject: str
    created_at: datetime


class BatchCreate(BaseModel):
    lot_number: str = Field(min_length=1, max_length=120)
    quantity: int = Field(gt=0, le=10_000_000)
    manufactured_on: date | None = None
    expires_on: date | None = None
    source_reference: str | None = Field(default=None, max_length=160)
    idempotency_key: str = Field(min_length=8, max_length=160)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.manufactured_on and self.expires_on and self.expires_on < self.manufactured_on:
            raise ValueError("Expiry date cannot be before manufacture date")
        return self


class Batch(BaseModel):
    id: UUID
    stock_item_id: UUID
    lot_number: str
    manufactured_on: date | None
    expires_on: date | None
    status: Literal["AVAILABLE", "HOLD", "RECALLED"]
    on_hand: int
    reserved: int
    available: int
    expired: bool
    created_at: datetime
    updated_at: datetime


class BatchStatusUpdate(BaseModel):
    status: Literal["AVAILABLE", "HOLD", "RECALLED"]
    reason: str = Field(min_length=3, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=160)


class ReservationAllocation(BaseModel):
    stock_item_id: UUID
    batch_id: UUID
    lot_number: str
    expires_on: date | None
    quantity: int


class ReservationLineCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=10000)


class ReservationCreate(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=160)
    source_reference: str = Field(min_length=1, max_length=160)
    ttl_seconds: int = Field(default=900, ge=60, le=3600)
    lines: list[ReservationLineCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_skus(self):
        if len({line.sku for line in self.lines}) != len(self.lines):
            raise ValueError("Reservation lines must contain unique SKUs")
        return self


class ReservationLine(BaseModel):
    stock_item_id: UUID
    sku: str
    quantity: int


class Reservation(BaseModel):
    id: UUID
    idempotency_key: str
    source_reference: str
    status: Literal["ACTIVE", "COMMITTED", "RELEASED", "EXPIRED"]
    expires_at: datetime
    lines: list[ReservationLine]
    allocations: list[ReservationAllocation] = Field(default_factory=list)


class InventoryDashboardSummary(BaseModel):
    tracked_products: int
    available_units: int
    reserved_units: int
    damaged_units: int
    low_stock_products: int
    out_of_stock_products: int
    expiring_within_60_days: int
    blocked_batches: int


class InventoryAlert(BaseModel):
    type: Literal["LOW_STOCK", "OUT_OF_STOCK", "EXPIRING"]
    stock_item_id: UUID
    sku: str
    available: int
    low_stock_threshold: int | None = None
    batch_id: UUID | None = None
    lot_number: str | None = None
    expires_on: date | None = None
