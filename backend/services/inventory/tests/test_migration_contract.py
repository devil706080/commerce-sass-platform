from pathlib import Path


def test_migration_enforces_inventory_invariants() -> None:
    sql = (Path(__file__).parents[1] / "migrations" / "001_inventory_core.sql").read_text()
    assert "reserved + damaged <= on_hand" in sql
    assert "idempotency_key varchar(160) NOT NULL UNIQUE" in sql
    assert "REVOKE ALL ON ALL TABLES" in sql
    assert "GRANT SELECT, INSERT, UPDATE" in sql


def test_batch_migration_supports_fefo_allocations_and_audit() -> None:
    sql = (Path(__file__).parents[1] / "migrations" / "002_batch_fefo.sql").read_text()
    assert "reservation_allocations" in sql
    assert "inventory_batches_fefo_idx" in sql
    assert "batch_events" in sql
    assert "receipt_idempotency_key" in sql
