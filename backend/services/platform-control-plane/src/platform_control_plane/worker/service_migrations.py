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
            "WHERE r.migration_status IN ('PENDING', 'FAILED') AND d.status='INFRASTRUCTURE_READY'"
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
