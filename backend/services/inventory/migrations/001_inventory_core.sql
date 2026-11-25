CREATE TABLE IF NOT EXISTS {schema}.inventory_schema_migrations (
    version integer PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.warehouses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(40) NOT NULL UNIQUE,
    name varchar(160) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.stock_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid NOT NULL,
    variant_id uuid,
    sku varchar(100) NOT NULL UNIQUE,
    warehouse_id uuid NOT NULL REFERENCES {schema}.warehouses(id),
    on_hand integer NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
    reserved integer NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    damaged integer NOT NULL DEFAULT 0 CHECK (damaged >= 0),
    low_stock_threshold integer NOT NULL DEFAULT 5 CHECK (low_stock_threshold >= 0),
    version integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (reserved + damaged <= on_hand)
);

ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS product_id uuid;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS variant_id uuid;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS warehouse_id uuid REFERENCES {schema}.warehouses(id);
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS on_hand integer NOT NULL DEFAULT 0;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS reserved integer NOT NULL DEFAULT 0;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS damaged integer NOT NULL DEFAULT 0;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS low_stock_threshold integer NOT NULL DEFAULT 5;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 0;
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE {schema}.stock_items ADD COLUMN IF NOT EXISTS available_quantity integer;
UPDATE {schema}.stock_items SET on_hand=available_quantity
WHERE on_hand=0 AND COALESCE(available_quantity,0)>0;
ALTER TABLE {schema}.stock_items DROP COLUMN IF EXISTS available_quantity;

CREATE TABLE IF NOT EXISTS {schema}.stock_movements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_item_id uuid NOT NULL REFERENCES {schema}.stock_items(id) ON DELETE RESTRICT,
    movement_type varchar(32) NOT NULL,
    quantity_delta integer NOT NULL CHECK (quantity_delta <> 0),
    reason varchar(500) NOT NULL,
    source_reference varchar(160),
    actor_subject varchar(255) NOT NULL,
    idempotency_key varchar(160) NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.batches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_item_id uuid NOT NULL REFERENCES {schema}.stock_items(id) ON DELETE RESTRICT,
    lot_number varchar(120) NOT NULL,
    manufactured_on date,
    expires_on date,
    status varchar(16) NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE','HOLD','RECALLED')),
    on_hand integer NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
    reserved integer NOT NULL DEFAULT 0 CHECK (reserved >= 0 AND reserved <= on_hand),
    UNIQUE(stock_item_id, lot_number)
);

CREATE TABLE IF NOT EXISTS {schema}.reservations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key varchar(160) NOT NULL UNIQUE,
    source_reference varchar(160) NOT NULL,
    status varchar(16) NOT NULL CHECK (status IN ('ACTIVE','COMMITTED','RELEASED','EXPIRED')),
    expires_at timestamptz NOT NULL,
    actor_subject varchar(255) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.reservation_lines (
    reservation_id uuid NOT NULL REFERENCES {schema}.reservations(id) ON DELETE RESTRICT,
    stock_item_id uuid NOT NULL REFERENCES {schema}.stock_items(id) ON DELETE RESTRICT,
    batch_id uuid REFERENCES {schema}.batches(id) ON DELETE RESTRICT,
    quantity integer NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (reservation_id, stock_item_id)
);

CREATE INDEX IF NOT EXISTS inventory_reservations_expiry_idx ON {schema}.reservations(expires_at) WHERE status='ACTIVE';
CREATE INDEX IF NOT EXISTS inventory_movements_stock_created_idx ON {schema}.stock_movements(stock_item_id, created_at DESC);

REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON {schema}.warehouses, {schema}.stock_items, {schema}.stock_movements, {schema}.batches, {schema}.reservations, {schema}.reservation_lines TO {runtime_role};
GRANT SELECT ON {schema}.inventory_schema_migrations TO {runtime_role};
ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE ALL ON TABLES FROM PUBLIC;

INSERT INTO {schema}.inventory_schema_migrations(version) VALUES (1) ON CONFLICT (version) DO NOTHING;
