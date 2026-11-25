ALTER TABLE {schema}.batches
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS receipt_idempotency_key varchar(160);

CREATE UNIQUE INDEX IF NOT EXISTS inventory_batches_receipt_idempotency_idx
    ON {schema}.batches(receipt_idempotency_key)
    WHERE receipt_idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS {schema}.reservation_allocations (
    reservation_id uuid NOT NULL REFERENCES {schema}.reservations(id) ON DELETE RESTRICT,
    stock_item_id uuid NOT NULL REFERENCES {schema}.stock_items(id) ON DELETE RESTRICT,
    batch_id uuid NOT NULL REFERENCES {schema}.batches(id) ON DELETE RESTRICT,
    quantity integer NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (reservation_id, batch_id)
);

CREATE TABLE IF NOT EXISTS {schema}.batch_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id uuid NOT NULL REFERENCES {schema}.batches(id) ON DELETE RESTRICT,
    previous_status varchar(16) NOT NULL,
    new_status varchar(16) NOT NULL,
    reason varchar(500) NOT NULL,
    actor_subject varchar(255) NOT NULL,
    idempotency_key varchar(160) NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS inventory_batches_fefo_idx
    ON {schema}.batches(stock_item_id, expires_on, created_at, id)
    WHERE status = 'AVAILABLE';

CREATE INDEX IF NOT EXISTS inventory_allocations_reservation_idx
    ON {schema}.reservation_allocations(reservation_id, stock_item_id);

REVOKE ALL ON TABLE {schema}.reservation_allocations FROM PUBLIC;
REVOKE ALL ON TABLE {schema}.batch_events FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON {schema}.reservation_allocations TO {runtime_role};
GRANT SELECT, INSERT, UPDATE ON {schema}.batches TO {runtime_role};
GRANT SELECT, INSERT ON {schema}.batch_events TO {runtime_role};

INSERT INTO {schema}.inventory_schema_migrations(version)
VALUES (2)
ON CONFLICT (version) DO NOTHING;
