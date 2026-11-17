import argparse
import logging
import time
from typing import Any
from uuid import UUID, uuid4

import psycopg

from platform_control_plane.core.config import WorkerSettings
from platform_control_plane.worker.provisioner import (
    create_database_infrastructure,
    database_identity,
    load_or_create_secrets,
)

logger = logging.getLogger("platform_control_plane.worker")


def _claim_job(connection: psycopg.Connection[Any]) -> dict[str, Any] | None:
    with connection.transaction():
        row = connection.execute(
            "SELECT id, tenant_id, service_key FROM provisioning_jobs "
            "WHERE status = 'PENDING' ORDER BY created_at, id "
            "FOR UPDATE SKIP LOCKED LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE provisioning_jobs SET status = 'RUNNING', attempt_count = attempt_count + 1, "
            "error_code = NULL, started_at = now(), completed_at = NULL, updated_at = now() "
            "WHERE id = %s",
            (row[0],),
        )
        return {"id": row[0], "tenant_id": row[1], "service_key": row[2]}


def process_one(settings: WorkerSettings) -> bool:
    worker_dsn = (
        settings.worker_database_url()
        .render_as_string(hide_password=False)
        .replace("postgresql+psycopg://", "postgresql://")
    )
    provisioner_dsn = (
        settings.provisioner_database_url()
        .render_as_string(hide_password=False)
        .replace("postgresql+psycopg://", "postgresql://")
    )
    with psycopg.connect(worker_dsn) as control:
        job = _claim_job(control)
        if job is None:
            return False
        try:
            job_id = UUID(str(job["id"]))
            tenant_id = UUID(str(job["tenant_id"]))
            identity = database_identity(tenant_id, str(job["service_key"]))
            credentials = load_or_create_secrets(settings.local_provisioned_secrets_dir, job_id)
            create_database_infrastructure(provisioner_dsn, identity, credentials)
            with control.transaction():
                control.execute(
                    "INSERT INTO tenant_databases (id, tenant_id, database_name, owner_role, secret_reference) "
                    "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (tenant_id) DO UPDATE SET "
                    "database_name=EXCLUDED.database_name, owner_role=EXCLUDED.owner_role, secret_reference=EXCLUDED.secret_reference, updated_at=now()",
                    (
                        uuid4(),
                        tenant_id,
                        identity.database_name,
                        identity.owner_role,
                        credentials.reference,
                    ),
                )
                control.execute(
                    "INSERT INTO tenant_service_databases "
                    "(id, tenant_id, service_key, tenant_database_id, schema_name, database_name, runtime_role, migrator_role, "
                    "secret_reference) VALUES (%s, %s, %s, (SELECT id FROM tenant_databases WHERE tenant_id=%s), %s, %s, %s, %s, %s) "
                    "ON CONFLICT (tenant_id, service_key) DO UPDATE SET "
                    "tenant_database_id = EXCLUDED.tenant_database_id, schema_name = EXCLUDED.schema_name, database_name = EXCLUDED.database_name, runtime_role = EXCLUDED.runtime_role, "
                    "migrator_role = EXCLUDED.migrator_role, "
                    "secret_reference = EXCLUDED.secret_reference, updated_at = now()",
                    (
                        uuid4(),
                        tenant_id,
                        job["service_key"],
                        tenant_id,
                        identity.schema_name,
                        identity.database_name,
                        identity.runtime_role,
                        identity.migrator_role,
                        credentials.reference,
                    ),
                )
                control.execute(
                    "INSERT INTO tenant_service_readiness (id, tenant_id, service_key) VALUES (%s, %s, %s) "
                    "ON CONFLICT (tenant_id, service_key) DO NOTHING",
                    (uuid4(), tenant_id, job["service_key"]),
                )
                control.execute(
                    "UPDATE provisioning_jobs SET status = 'INFRASTRUCTURE_READY', "
                    "completed_at = now(), updated_at = now() WHERE id = %s",
                    (job_id,),
                )
            logger.info("provisioning_job_completed job_id=%s", job_id)
        except Exception:  # noqa: BLE001 - persist a generic failure without leaking details
            control.rollback()
            with control.transaction():
                control.execute(
                    "UPDATE provisioning_jobs SET status = 'FAILED', "
                    "error_code = 'PROVISIONING_FAILED', completed_at = now(), updated_at = now() "
                    "WHERE id = %s",
                    (job["id"],),
                )
            logger.error("provisioning_job_failed job_id=%s", job["id"])
        return True


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = WorkerSettings()  # type: ignore[call-arg]
    logging.basicConfig(level=logging.INFO)
    while True:
        processed = process_one(settings)
        if args.once:
            return
        if not processed:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    run()
