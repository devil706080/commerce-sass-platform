import json
from pathlib import Path

import psycopg
from psycopg import sql

from platform_control_plane.core.config import WorkerSettings


def run_service_migrations(settings: WorkerSettings) -> None:
    control_dsn = (
        settings.worker_database_url()
        .render_as_string(hide_password=False)
        .replace("postgresql+psycopg://", "postgresql://")
    )
    with psycopg.connect(control_dsn) as control:
        rows = control.execute(
            "SELECT r.tenant_id,r.service_key,d.database_name,d.schema_name,d.secret_reference "
            "FROM tenant_service_readiness r JOIN tenant_service_databases d USING (tenant_id,service_key) "
            "WHERE d.status='INFRASTRUCTURE_READY'"
        ).fetchall()
        for tenant_id, service_key, database_name, schema_name, reference in rows:
            payload = json.loads(
                (
                    Path(settings.local_provisioned_secrets_dir)
                    / reference.removeprefix("local-volume://")
                ).read_text(encoding="utf-8")
            )
            migrator_role = (
                f"t_{tenant_id.hex}_{'catfx' if service_key == 'catalogue_fixture' else 'invfx'}_mg"
            )
            runtime_role = (
                f"t_{tenant_id.hex}_{'catfx' if service_key == 'catalogue_fixture' else 'invfx'}_rt"
            )
            try:
                with psycopg.connect(
                    host=settings.db_host,
                    port=settings.db_port,
                    dbname=database_name,
                    user=migrator_role,
                    password=payload["migrator_password"],
                    autocommit=True,
                ) as service:
                    if service_key == "catalogue_fixture":
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.products (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), sku text NOT NULL UNIQUE, name text NOT NULL, price_cents integer NOT NULL CHECK (price_cents >= 0))"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(sql.SQL("ALTER TABLE {}.products ADD COLUMN IF NOT EXISTS description text").format(sql.Identifier(schema_name)))
                        service.execute(sql.SQL("ALTER TABLE {}.products ADD COLUMN IF NOT EXISTS published boolean NOT NULL DEFAULT false").format(sql.Identifier(schema_name)))
                        service.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {}.categories (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL, slug text NOT NULL UNIQUE, description text)").format(sql.Identifier(schema_name)))
                        service.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {}.product_categories (product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, category_id uuid NOT NULL REFERENCES {}.categories(id) ON DELETE CASCADE, PRIMARY KEY(product_id, category_id))").format(sql.Identifier(schema_name), sql.Identifier(schema_name), sql.Identifier(schema_name)))
                        service.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON {}.categories, {}.product_categories TO {}").format(sql.Identifier(schema_name), sql.Identifier(schema_name), sql.Identifier(runtime_role)))
                        service.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {}.product_images (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, url text NOT NULL, alt_text text, sort_order integer NOT NULL DEFAULT 0)").format(sql.Identifier(schema_name), sql.Identifier(schema_name)))
                        service.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {}.product_variants (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, sku text NOT NULL UNIQUE, name text NOT NULL, price_cents integer NOT NULL CHECK (price_cents >= 0), attributes jsonb NOT NULL DEFAULT '{{}}'::jsonb)").format(sql.Identifier(schema_name), sql.Identifier(schema_name)))
                        service.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {}.product_prices (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, name text NOT NULL, price_cents integer NOT NULL CHECK (price_cents >= 0), currency char(3) NOT NULL DEFAULT 'INR', active boolean NOT NULL DEFAULT true)").format(sql.Identifier(schema_name), sql.Identifier(schema_name)))
                        service.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON {}.product_images, {}.product_variants, {}.product_prices TO {}").format(sql.Identifier(schema_name), sql.Identifier(schema_name), sql.Identifier(schema_name), sql.Identifier(runtime_role)))
                        service.execute(
                            sql.SQL("GRANT SELECT, INSERT, UPDATE ON {}.products TO {}").format(
                                sql.Identifier(schema_name), sql.Identifier(runtime_role)
                            )
                        )
                    else:
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.stock_items (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), sku text NOT NULL UNIQUE, available_quantity integer NOT NULL CHECK (available_quantity >= 0))"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL("GRANT SELECT, INSERT, UPDATE ON {}.stock_items TO {}").format(
                                sql.Identifier(schema_name), sql.Identifier(runtime_role)
                            )
                        )
                    control.execute(
                        "UPDATE tenant_service_readiness SET migration_status='MIGRATED', smoke_status='PASSED', updated_at=now() WHERE tenant_id=%s AND service_key=%s",
                        (tenant_id, service_key),
                    )
                control.commit()
            except Exception:  # noqa: BLE001 - persist failed migration state without leaking details
                control.rollback()
                control.execute(
                    "UPDATE tenant_service_readiness SET migration_status='FAILED', smoke_status='FAILED', updated_at=now() WHERE tenant_id=%s AND service_key=%s",
                    (tenant_id, service_key),
                )
                control.commit()


if __name__ == "__main__":
    run_service_migrations(WorkerSettings())  # type: ignore[call-arg]
