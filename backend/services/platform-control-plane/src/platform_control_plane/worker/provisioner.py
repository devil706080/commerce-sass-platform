import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql

SERVICE_CODES = {
    "catalogue_fixture": "catfx",
    "inventory_fixture": "invfx",
    "media_fixture": "medfx",
    "identity_access": "identity",
}


@dataclass(frozen=True)
class DatabaseIdentity:
    database_name: str
    owner_role: str
    schema_name: str
    runtime_role: str
    migrator_role: str


@dataclass(frozen=True)
class ServiceSecrets:
    runtime_password: str
    migrator_password: str
    reference: str


def database_identity(tenant_id: UUID, service_key: str) -> DatabaseIdentity:
    try:
        code = SERVICE_CODES[service_key]
    except KeyError as exc:
        raise ValueError("unsupported service key") from exc
    opaque = tenant_id.hex
    base = f"t_{opaque}"
    return DatabaseIdentity(base, f"{base}_owner", code, f"{base}_{code}_rt", f"{base}_{code}_mg")


def load_or_create_secrets(directory: str, job_id: UUID) -> ServiceSecrets:
    root = Path(directory)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = root / f"{job_id}.json"
    reference = f"local-volume://{path.name}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        payload = {
            "runtime_password": secrets.token_urlsafe(32),
            "migrator_password": secrets.token_urlsafe(32),
        }
        temporary = path.with_suffix(".tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            os.replace(temporary, path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    if set(payload) != {"runtime_password", "migrator_password"}:
        raise ValueError("invalid local secret payload")
    return ServiceSecrets(payload["runtime_password"], payload["migrator_password"], reference)


def create_database_infrastructure(
    provisioner_dsn: str,
    identity: DatabaseIdentity,
    credentials: ServiceSecrets,
) -> None:
    with psycopg.connect(provisioner_dsn, autocommit=True) as connection:
        for role, password in (
            (identity.runtime_role, credentials.runtime_password),
            (identity.migrator_role, credentials.migrator_password),
            (identity.owner_role, secrets.token_urlsafe(32)),
        ):
            exists = connection.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)", (role,)
            ).fetchone()
            if exists and exists[0]:
                connection.execute(
                    sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                        sql.Identifier(role), sql.Literal(password)
                    )
                )
            else:
                login_clause = "NOLOGIN" if role == identity.owner_role else "LOGIN"
                connection.execute(
                    sql.SQL(
                        "CREATE ROLE {} " + login_clause + " PASSWORD {} NOSUPERUSER NOCREATEDB "
                        "NOCREATEROLE NOREPLICATION CONNECTION LIMIT 20"
                    ).format(sql.Identifier(role), sql.Literal(password))
                )
        # Reassert SET membership on every idempotent retry. Earlier local runs may have left
        # a membership without SET OPTION; membership alone cannot create a database owned by
        # this generated role.
        connection.execute(
            sql.SQL("GRANT {} TO tenant_database_provisioner WITH SET TRUE").format(
                sql.Identifier(identity.owner_role)
            )
        )
        try:
            exists = connection.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = %s)",
                (identity.database_name,),
            ).fetchone()
            if not exists or not exists[0]:
                connection.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(identity.database_name), sql.Identifier(identity.owner_role)
                    )
                )
            connection.execute(
                sql.SQL("REVOKE CONNECT, TEMPORARY ON DATABASE {} FROM PUBLIC").format(
                    sql.Identifier(identity.database_name)
                )
            )
            connection.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}, {}").format(
                    sql.Identifier(identity.database_name),
                    sql.Identifier(identity.runtime_role),
                    sql.Identifier(identity.migrator_role),
                )
            )
            connection.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO tenant_database_provisioner").format(
                    sql.Identifier(identity.database_name)
                )
            )
            connection.execute(
                sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                    sql.Identifier(identity.database_name), sql.Identifier(identity.owner_role)
                )
            )
        except BaseException:
            connection.execute(
                sql.SQL("REVOKE {} FROM tenant_database_provisioner").format(
                    sql.Identifier(identity.owner_role)
                )
            )
            raise
    try:
        with psycopg.connect(
            provisioner_dsn, dbname=identity.database_name, autocommit=True
        ) as tenant_connection:
            tenant_connection.execute(
                sql.SQL("SET ROLE {}").format(sql.Identifier(identity.owner_role))
            )
            tenant_connection.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}").format(
                    sql.Identifier(identity.schema_name), sql.Identifier(identity.owner_role)
                )
            )
            tenant_connection.execute(
                sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(
                    sql.Identifier(identity.schema_name)
                )
            )
            tenant_connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(identity.schema_name), sql.Identifier(identity.runtime_role)
                )
            )
            tenant_connection.execute(
                sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}").format(
                    sql.Identifier(identity.schema_name), sql.Identifier(identity.migrator_role)
                )
            )
    finally:
        with psycopg.connect(provisioner_dsn, autocommit=True) as connection:
            connection.execute(
                sql.SQL("REVOKE {} FROM tenant_database_provisioner").format(
                    sql.Identifier(identity.owner_role)
                )
            )
            connection.execute(
                sql.SQL("REVOKE CONNECT ON DATABASE {} FROM tenant_database_provisioner").format(
                    sql.Identifier(identity.database_name)
                )
            )
