import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    schema: str
    storage_root: Path
    issuer: str
    audience: str
    jwks_url: str
    max_upload_bytes: int
    max_pixels: int


def load_settings() -> Settings:
    database_url = os.getenv("MEDIA_DATABASE_URL")
    secret_file = os.getenv("MEDIA_SECRET_FILE")
    if not database_url and secret_file:
        secret = json.loads(Path(secret_file).read_text(encoding="utf-8"))
        database_url = "postgresql://{}:{}@{}:{}/{}".format(
            quote_plus(os.environ["MEDIA_RUNTIME_ROLE"]), quote_plus(secret["runtime_password"]),
            os.getenv("MEDIA_DB_HOST", "postgres"), os.getenv("MEDIA_DB_PORT", "5432"), os.environ["MEDIA_DATABASE_NAME"],
        )
    return Settings(database_url, os.getenv("MEDIA_SCHEMA", "medfx"), Path(os.getenv("MEDIA_STORAGE_ROOT", "/var/lib/commerce-media")), os.getenv("MEDIA_OIDC_ISSUER", ""), os.getenv("MEDIA_OIDC_AUDIENCE", ""), os.getenv("MEDIA_OIDC_JWKS_URL", ""), int(os.getenv("MEDIA_MAX_UPLOAD_BYTES", "5242880")), int(os.getenv("MEDIA_MAX_PIXELS", "20000000")))
