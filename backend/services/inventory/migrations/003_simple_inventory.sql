ALTER TABLE {schema}.stock_items
    ADD COLUMN IF NOT EXISTS tracking_mode varchar(24) NOT NULL DEFAULT 'SIMPLE';

ALTER TABLE {schema}.stock_items
    DROP CONSTRAINT IF EXISTS inventory_stock_items_tracking_mode_check;

ALTER TABLE {schema}.stock_items
    ADD CONSTRAINT inventory_stock_items_tracking_mode_check
    CHECK (tracking_mode IN ('SIMPLE', 'BATCH_EXPIRY'));

INSERT INTO {schema}.warehouses(code, name, active)
VALUES ('MAIN', 'Main Location', true)
ON CONFLICT (code) DO NOTHING;

INSERT INTO {schema}.inventory_schema_migrations(version)
VALUES (3)
ON CONFLICT (version) DO NOTHING;
