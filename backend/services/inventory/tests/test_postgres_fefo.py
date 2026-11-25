import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import uuid4

import psycopg
import pytest

from inventory.config import Settings
from inventory.errors import InventoryConflict
from inventory.repository import InventoryRepository
from inventory.schemas import BatchCreate, ReservationCreate, StockItemCreate, WarehouseCreate


pytestmark = pytest.mark.integration


@dataclass
class InventoryTestContext:
    repository: InventoryRepository
    warehouse_ids: list = field(default_factory=list)
    stock_item_ids: list = field(default_factory=list)
    batch_ids: list = field(default_factory=list)
    reservation_ids: list = field(default_factory=list)


@pytest.fixture()
def repository():
    migrator_url = os.getenv("INVENTORY_TEST_MIGRATOR_DATABASE_URL")
    runtime_url = os.getenv("INVENTORY_TEST_RUNTIME_DATABASE_URL")
    runtime_role = os.getenv("INVENTORY_TEST_RUNTIME_ROLE")
    if not migrator_url or not runtime_url or not runtime_role:
        pytest.skip("Inventory PostgreSQL test credentials are not configured")

    schema_name = os.getenv("INVENTORY_TEST_SCHEMA", "invfx")
    assert schema_name.replace("_", "").isalnum()
    context = InventoryTestContext(
        InventoryRepository(Settings(database_url=runtime_url, schema_name=schema_name))
    )
    try:
        yield context
    finally:
        with psycopg.connect(migrator_url, autocommit=True) as connection:
            if context.reservation_ids:
                connection.execute(
                    f"DELETE FROM {schema_name}.reservation_allocations WHERE reservation_id=ANY(%s)",
                    (context.reservation_ids,),
                )
                connection.execute(
                    f"DELETE FROM {schema_name}.reservation_lines WHERE reservation_id=ANY(%s)",
                    (context.reservation_ids,),
                )
                connection.execute(
                    f"DELETE FROM {schema_name}.reservations WHERE id=ANY(%s)",
                    (context.reservation_ids,),
                )
            if context.batch_ids:
                connection.execute(
                    f"DELETE FROM {schema_name}.batch_events WHERE batch_id=ANY(%s)",
                    (context.batch_ids,),
                )
            if context.stock_item_ids:
                connection.execute(
                    f"DELETE FROM {schema_name}.stock_movements WHERE stock_item_id=ANY(%s)",
                    (context.stock_item_ids,),
                )
            if context.batch_ids:
                connection.execute(
                    f"DELETE FROM {schema_name}.batches WHERE id=ANY(%s)",
                    (context.batch_ids,),
                )
            if context.stock_item_ids:
                connection.execute(
                    f"DELETE FROM {schema_name}.stock_items WHERE id=ANY(%s)",
                    (context.stock_item_ids,),
                )
            if context.warehouse_ids:
                connection.execute(
                    f"DELETE FROM {schema_name}.warehouses WHERE id=ANY(%s)",
                    (context.warehouse_ids,),
                )


def _stock(context: InventoryTestContext, sku: str):
    warehouse = context.repository.create_warehouse(
        WarehouseCreate(code=f"W-{uuid4().hex[:8].upper()}", name="Integration warehouse")
    )
    context.warehouse_ids.append(warehouse["id"])
    item = context.repository.create_stock_item(
        StockItemCreate(
            product_id=uuid4(), sku=sku, warehouse_id=warehouse["id"], low_stock_threshold=1
        )
    )
    context.stock_item_ids.append(item["id"])
    return item


def test_reservation_allocates_earliest_expiry_first(
    repository: InventoryTestContext,
) -> None:
    item = _stock(repository, f"FEFO-{uuid4().hex[:8]}")
    later = repository.repository.create_batch(
        item["id"],
        BatchCreate(
            lot_number="LATER",
            quantity=5,
            expires_on=date.today() + timedelta(days=90),
            idempotency_key=f"receipt-{uuid4()}",
        ),
        "integration-test",
    )
    repository.batch_ids.append(later["id"])
    earlier = repository.repository.create_batch(
        item["id"],
        BatchCreate(
            lot_number="EARLIER",
            quantity=5,
            expires_on=date.today() + timedelta(days=30),
            idempotency_key=f"receipt-{uuid4()}",
        ),
        "integration-test",
    )
    repository.batch_ids.append(earlier["id"])
    reservation = repository.repository.reserve(
        ReservationCreate(
            idempotency_key=f"reserve-{uuid4()}",
            source_reference=f"order-{uuid4()}",
            lines=[{"sku": item["sku"], "quantity": 7}],
        ),
        "integration-test",
    )
    repository.reservation_ids.append(reservation["id"])

    assert [(row["batch_id"], row["quantity"]) for row in reservation["allocations"]] == [
        (earlier["id"], 5),
        (later["id"], 2),
    ]


def test_concurrent_reservations_do_not_oversell(repository: InventoryTestContext) -> None:
    item = _stock(repository, f"RACE-{uuid4().hex[:8]}")
    batch = repository.repository.create_batch(
        item["id"],
        BatchCreate(
            lot_number="ONLY-ONE",
            quantity=1,
            expires_on=date.today() + timedelta(days=30),
            idempotency_key=f"receipt-{uuid4()}",
        ),
        "integration-test",
    )
    repository.batch_ids.append(batch["id"])

    def reserve_once():
        try:
            reservation = repository.repository.reserve(
                ReservationCreate(
                    idempotency_key=f"reserve-{uuid4()}",
                    source_reference=f"order-{uuid4()}",
                    lines=[{"sku": item["sku"], "quantity": 1}],
                ),
                "integration-test",
            )
            repository.reservation_ids.append(reservation["id"])
            return "reserved"
        except InventoryConflict:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = sorted(executor.map(lambda _: reserve_once(), range(2)))
    assert results == ["rejected", "reserved"]


@pytest.mark.parametrize(
    "environment_name",
    ["INVENTORY_TEST_CROSS_TENANT_URL_A", "INVENTORY_TEST_CROSS_TENANT_URL_B"],
)
def test_cross_tenant_database_access_is_denied(environment_name: str) -> None:
    database_url = os.getenv(environment_name)
    if not database_url:
        pytest.skip("Cross-tenant Inventory database credentials are not configured")
    with pytest.raises(psycopg.OperationalError):
        psycopg.connect(database_url, connect_timeout=3)
