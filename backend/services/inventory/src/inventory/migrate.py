import os
import json
from pathlib import Path
from urllib.parse import quote_plus

import psycopg
from psycopg import sql


def safe_identifier(value: str) -> str:
    if not value or not value.replace("_", "").isalnum():
        raise ValueError("Invalid migration identifier")
    return sql.Identifier(value).as_string()


def migrate() -> None:
    database_url = os.getenv("INVENTORY_MIGRATOR_DATABASE_URL")
    if not database_url:
        secret_path = Path(os.environ["INVENTORY_SECRET_FILE"])
        secret = json.loads(secret_path.read_text(encoding="utf-8"))
        database_url = "postgresql://{}:{}@{}:{}/{}".format(
            quote_plus(os.environ["INVENTORY_MIGRATOR_ROLE"]),
            quote_plus(secret["migrator_password"]),
            os.getenv("INVENTORY_DB_HOST", "postgres"),
            int(os.getenv("INVENTORY_DB_PORT", "5432")),
            os.environ["INVENTORY_DATABASE_NAME"],
        )
    schema = safe_identifier(os.getenv("INVENTORY_SCHEMA", "invfx"))
    runtime_role = safe_identifier(os.environ["INVENTORY_RUNTIME_ROLE"])
    with psycopg.connect(database_url, autocommit=True) as connection:
        for migration_path in sorted((Path(__file__).parents[2] / "migrations").glob("[0-9][0-9][0-9]_*.sql")):
            migration = migration_path.read_text(encoding="utf-8")
            statement = migration.replace("{schema}", schema).replace(
                "{runtime_role}", runtime_role
            )
            connection.execute(statement)


if __name__ == "__main__":
    migrate()
