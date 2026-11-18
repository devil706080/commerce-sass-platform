from uuid import UUID
import psycopg
from fastapi import HTTPException
from media.config import Settings


def _schema(value: str) -> str:
    if not value.replace("_", "").isalnum(): raise ValueError("invalid schema")
    return f'"{value}"'


class MediaRepository:
    def __init__(self, settings: Settings):
        self.settings, self.schema = settings, _schema(settings.schema)

    def _connect(self):
        if not self.settings.database_url: raise HTTPException(503, "Media database is not configured")
        return psycopg.connect(self.settings.database_url)

    def create(self, asset_id: UUID, filename: str, size: int, width: int, height: int, key: str) -> None:
        with self._connect() as db:
            db.execute(f"INSERT INTO {self.schema}.assets(id,original_filename,content_type,byte_size,width,height,storage_key) VALUES(%s,%s,'image/webp',%s,%s,%s,%s)", (asset_id, filename, size, width, height, key)); db.commit()

    def get(self, asset_id: UUID):
        with self._connect() as db:
            row = db.execute(f"SELECT storage_key,content_type,byte_size,width,height FROM {self.schema}.assets WHERE id=%s", (asset_id,)).fetchone()
        if row is None: raise LookupError("Media asset not found")
        return row

    def delete(self, asset_id: UUID) -> str:
        with self._connect() as db:
            row = db.execute(f"DELETE FROM {self.schema}.assets WHERE id=%s RETURNING storage_key", (asset_id,)).fetchone(); db.commit()
        if row is None: raise LookupError("Media asset not found")
        return row[0]
