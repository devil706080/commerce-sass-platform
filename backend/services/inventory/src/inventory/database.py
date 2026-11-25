import psycopg
from fastapi import HTTPException
from inventory.config import Settings


class InventoryConnection:
    """Small adapter allowing a per-query row factory without changing transaction semantics."""

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, query, params=None, *, row_factory=None):
        if row_factory is not None:
            return self.connection.cursor(row_factory=row_factory).execute(query, params)
        return self.connection.execute(query, params)

    def commit(self):
        return self.connection.commit()

    def rollback(self):
        return self.connection.rollback()


def identifier(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError("invalid SQL identifier")
    return f'"{value}"'


def connect(settings: Settings):
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="Inventory database is not configured")
    return InventoryConnection(psycopg.connect(settings.database_url))
