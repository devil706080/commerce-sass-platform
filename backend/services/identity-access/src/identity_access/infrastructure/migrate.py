from pathlib import Path

import psycopg
from psycopg import sql

from identity_access.config.settings import Settings, load_settings


def migrate(settings: Settings) -> None:
    source = (Path(__file__).parents[3] / "migrations" / "001_staff_identity.sql").read_text(
        encoding="utf-8"
    )
    statement = sql.SQL(source).format(
        schema=sql.Identifier(settings.schema_name),
        runtime_role=sql.Identifier(settings.runtime_role),
    )
    with psycopg.connect(settings.database_url("migrator_password"), autocommit=True) as connection:
        connection.execute(statement)


if __name__ == "__main__":
    migrate(load_settings())
