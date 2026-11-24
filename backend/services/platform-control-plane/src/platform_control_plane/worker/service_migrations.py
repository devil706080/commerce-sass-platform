import json
from pathlib import Path

import psycopg
from psycopg import sql

from platform_control_plane.core.config import WorkerSettings

OWNED_SERVICE_KEYS = (
    "catalogue_fixture",
    "inventory_fixture",
    "identity_access",
    "media_fixture",
)
SERVICE_CODES = {
    "catalogue_fixture": "catfx",
    "inventory_fixture": "invfx",
    "identity_access": "identity",
    "media_fixture": "medfx",
}
CATALOGUE_PRODUCT_RUNTIME_PRIVILEGES = "SELECT, INSERT, UPDATE, DELETE"


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
            "WHERE d.status='INFRASTRUCTURE_READY' AND r.service_key = ANY(%s)",
            (list(OWNED_SERVICE_KEYS),),
        ).fetchall()
        for tenant_id, service_key, database_name, schema_name, reference in rows:
            payload = json.loads(
                (
                    Path(settings.local_provisioned_secrets_dir)
                    / reference.removeprefix("local-volume://")
                ).read_text(encoding="utf-8")
            )
            service_code = SERVICE_CODES[service_key]
            migrator_role = f"t_{tenant_id.hex}_{service_code}_mg"
            runtime_role = f"t_{tenant_id.hex}_{service_code}_rt"
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
                        service.execute(
                            sql.SQL(
                                "ALTER TABLE {}.products ADD COLUMN IF NOT EXISTS description text"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "ALTER TABLE {}.products ADD COLUMN IF NOT EXISTS published boolean NOT NULL DEFAULT false"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.categories (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL, slug text NOT NULL UNIQUE, description text)"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.product_categories (product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, category_id uuid NOT NULL REFERENCES {}.categories(id) ON DELETE CASCADE, PRIMARY KEY(product_id, category_id))"
                            ).format(
                                sql.Identifier(schema_name),
                                sql.Identifier(schema_name),
                                sql.Identifier(schema_name),
                            )
                        )
                        service.execute(
                            sql.SQL(
                                "GRANT SELECT, INSERT, UPDATE, DELETE ON {}.categories, {}.product_categories TO {}"
                            ).format(
                                sql.Identifier(schema_name),
                                sql.Identifier(schema_name),
                                sql.Identifier(runtime_role),
                            )
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.product_images (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, url text NOT NULL, alt_text text, sort_order integer NOT NULL DEFAULT 0)"
                            ).format(sql.Identifier(schema_name), sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.product_variants (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, sku text NOT NULL UNIQUE, name text NOT NULL, price_cents integer NOT NULL CHECK (price_cents >= 0), attributes jsonb NOT NULL DEFAULT '{{}}'::jsonb)"
                            ).format(sql.Identifier(schema_name), sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.product_prices (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), product_id uuid NOT NULL REFERENCES {}.products(id) ON DELETE CASCADE, name text NOT NULL, price_cents integer NOT NULL CHECK (price_cents >= 0), currency char(3) NOT NULL DEFAULT 'INR', active boolean NOT NULL DEFAULT true)"
                            ).format(sql.Identifier(schema_name), sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "GRANT SELECT, INSERT, UPDATE, DELETE ON {}.product_images, {}.product_variants, {}.product_prices TO {}"
                            ).format(
                                sql.Identifier(schema_name),
                                sql.Identifier(schema_name),
                                sql.Identifier(schema_name),
                                sql.Identifier(runtime_role),
                            )
                        )
                        service.execute(
                            sql.SQL("GRANT {} ON {}.products TO {}").format(
                                sql.SQL(CATALOGUE_PRODUCT_RUNTIME_PRIVILEGES),
                                sql.Identifier(schema_name),
                                sql.Identifier(runtime_role),
                            )
                        )
                    elif service_key == "inventory_fixture":
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
                    elif service_key == "identity_access":
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.identity_schema_migrations (version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.identity_principals (id uuid PRIMARY KEY, issuer text NOT NULL, subject text NOT NULL, email varchar(320) NOT NULL, display_name varchar(200), created_at timestamptz NOT NULL DEFAULT now(), last_seen_at timestamptz NOT NULL DEFAULT now(), CONSTRAINT uq_identity_principal_subject UNIQUE (issuer, subject))"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.staff_invitations (id uuid PRIMARY KEY, email varchar(320) NOT NULL, role varchar(32) NOT NULL, status varchar(16) NOT NULL DEFAULT 'PENDING', invited_by_issuer text NOT NULL, invited_by_subject text NOT NULL, expires_at timestamptz NOT NULL DEFAULT (now() + interval '7 days'), created_at timestamptz NOT NULL DEFAULT now(), accepted_at timestamptz, CONSTRAINT ck_staff_invitation_role CHECK (role IN ('TENANT_OWNER','TENANT_ADMIN','CATALOGUE_MANAGER','ORDER_MANAGER','VIEWER')), CONSTRAINT ck_staff_invitation_status CHECK (status IN ('PENDING','ACCEPTED','REVOKED','EXPIRED')))"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE UNIQUE INDEX IF NOT EXISTS {} ON {}.staff_invitations (lower(email)) WHERE status = 'PENDING'"
                            ).format(
                                sql.Identifier("uq_pending_staff_invitation_email"),
                                sql.Identifier(schema_name),
                            )
                        )
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.staff_memberships (id uuid PRIMARY KEY, principal_id uuid NOT NULL REFERENCES {}.identity_principals(id) ON DELETE CASCADE, role varchar(32) NOT NULL, status varchar(16) NOT NULL DEFAULT 'ACTIVE', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), CONSTRAINT uq_staff_membership_principal UNIQUE (principal_id), CONSTRAINT ck_staff_membership_role CHECK (role IN ('TENANT_OWNER','TENANT_ADMIN','CATALOGUE_MANAGER','ORDER_MANAGER','VIEWER')), CONSTRAINT ck_staff_membership_status CHECK (status IN ('ACTIVE','SUSPENDED','REVOKED')))"
                            ).format(sql.Identifier(schema_name), sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM PUBLIC").format(
                                sql.Identifier(schema_name)
                            )
                        )
                        service.execute(
                            sql.SQL(
                                "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {} TO {}"
                            ).format(sql.Identifier(schema_name), sql.Identifier(runtime_role))
                        )
                        service.execute(
                            sql.SQL(
                                "ALTER DEFAULT PRIVILEGES IN SCHEMA {} REVOKE ALL ON TABLES FROM PUBLIC"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL(
                                "INSERT INTO {}.identity_schema_migrations(version) VALUES (1) ON CONFLICT (version) DO NOTHING"
                            ).format(sql.Identifier(schema_name))
                        )
                    elif service_key == "media_fixture":
                        service.execute(
                            sql.SQL(
                                "CREATE TABLE IF NOT EXISTS {}.assets (id uuid PRIMARY KEY, original_filename text NOT NULL, content_type text NOT NULL CHECK (content_type = 'image/webp'), byte_size integer NOT NULL CHECK (byte_size > 0), width integer NOT NULL CHECK (width > 0), height integer NOT NULL CHECK (height > 0), storage_key text NOT NULL UNIQUE, created_at timestamptz NOT NULL DEFAULT now())"
                            ).format(sql.Identifier(schema_name))
                        )
                        service.execute(
                            sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM PUBLIC").format(
                                sql.Identifier(schema_name)
                            )
                        )
                        service.execute(
                            sql.SQL(
                                "GRANT SELECT, INSERT, UPDATE, DELETE ON {}.assets TO {}"
                            ).format(sql.Identifier(schema_name), sql.Identifier(runtime_role))
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
