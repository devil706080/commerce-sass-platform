import os
from dataclasses import dataclass
from pathlib import Path


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
    tenant_context_signing_secret: str
    provisioned_secrets_dir: Path
    db_host: str
    db_port: int


def load_settings() -> Settings:
    return Settings(
        database_url=None,
        schema=os.getenv("MEDIA_SCHEMA", "medfx"),
        storage_root=Path(os.getenv("MEDIA_STORAGE_ROOT", "/var/lib/commerce-media")),
        issuer=os.getenv("MEDIA_OIDC_ISSUER", ""),
        audience=os.getenv("MEDIA_OIDC_AUDIENCE", ""),
        jwks_url=os.getenv("MEDIA_OIDC_JWKS_URL", ""),
        max_upload_bytes=int(os.getenv("MEDIA_MAX_UPLOAD_BYTES", "5242880")),
        max_pixels=int(os.getenv("MEDIA_MAX_PIXELS", "20000000")),
        tenant_context_signing_secret=os.getenv("TENANT_CONTEXT_SIGNING_SECRET", ""),
        provisioned_secrets_dir=Path(
            os.getenv("PROVISIONED_SECRETS_DIR", "/var/lib/platform-secrets")
        ),
        db_host=os.getenv("MEDIA_DB_HOST", "postgres"),
        db_port=int(os.getenv("MEDIA_DB_PORT", "5432")),
    )
