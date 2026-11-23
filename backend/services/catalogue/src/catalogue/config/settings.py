import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    database_url: str | None
    schema_name: str
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    tenant_context_signing_secret: str = ""
    provisioned_secrets_dir: Path = Path("/var/lib/platform-secrets")
    db_host: str = "postgres"
    db_port: int = 5432

def load_settings() -> Settings:
    return Settings(
        database_url=None,
        schema_name=os.getenv("CATALOGUE_SCHEMA", "catfx"),
        oidc_issuer=os.getenv("CATALOGUE_OIDC_ISSUER", ""),
        oidc_audience=os.getenv("CATALOGUE_OIDC_AUDIENCE", ""),
        oidc_jwks_url=os.getenv("CATALOGUE_OIDC_JWKS_URL", ""),
        tenant_context_signing_secret=os.getenv("TENANT_CONTEXT_SIGNING_SECRET", ""),
        provisioned_secrets_dir=Path(
            os.getenv("PROVISIONED_SECRETS_DIR", "/var/lib/platform-secrets")
        ),
        db_host=os.getenv("CATALOGUE_DB_HOST", "postgres"),
        db_port=int(os.getenv("CATALOGUE_DB_PORT", "5432")),
    )
