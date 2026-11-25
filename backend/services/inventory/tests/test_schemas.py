from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from inventory.schemas import AdjustmentCreate, BatchCreate, ReservationCreate


def test_reservation_rejects_duplicate_skus() -> None:
    with pytest.raises(ValidationError, match="unique SKUs"):
        ReservationCreate(
            idempotency_key="checkout-12345",
            source_reference=str(uuid4()),
            lines=[{"sku": "SKU-1", "quantity": 1}, {"sku": "SKU-1", "quantity": 2}],
        )


def test_reservation_ttl_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ReservationCreate(
            idempotency_key="checkout-12345",
            source_reference=str(uuid4()),
            ttl_seconds=30,
            lines=[{"sku": "SKU-1", "quantity": 1}],
        )


def test_adjustment_requires_nonzero_quantity_and_reason() -> None:
    with pytest.raises(ValidationError):
        AdjustmentCreate(quantity_delta=0, reason="", idempotency_key="adjust-12345")


def test_batch_rejects_expiry_before_manufacture() -> None:
    with pytest.raises(ValidationError):
        BatchCreate(
            lot_number="LOT-1",
            quantity=10,
            manufactured_on=date(2027, 2, 1),
            expires_on=date(2027, 1, 1),
            idempotency_key="receipt-0001",
        )
