import os
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str | None = None
    schema_name: str = "invfx"
    oidc_issuer: str = ""
    oidc_audience: str = "inventory-api"
    oidc_jwks_url: str = ""
    tenant_context_signing_secret: str = ""
    provisioned_secrets_dir: Path = Path("/var/lib/platform-secrets")
    db_host: str = "postgres"
    db_port: int = 5432

    def with_database(self, database_url: str, schema_name: str) -> "Settings":
        return replace(self, database_url=database_url, schema_name=schema_name)


def load_settings() -> Settings:
    return Settings(
        schema_name=os.getenv("INVENTORY_SCHEMA", "invfx"),
        oidc_issuer=os.getenv("INVENTORY_OIDC_ISSUER", ""),
        oidc_audience=os.getenv("INVENTORY_OIDC_AUDIENCE", "inventory-api"),
        oidc_jwks_url=os.getenv("INVENTORY_OIDC_JWKS_URL", ""),
        tenant_context_signing_secret=os.getenv("TENANT_CONTEXT_SIGNING_SECRET", ""),
        provisioned_secrets_dir=Path(os.getenv("PROVISIONED_SECRETS_DIR", "/var/lib/platform-secrets")),
        db_host=os.getenv("INVENTORY_DB_HOST", "postgres"),
        db_port=int(os.getenv("INVENTORY_DB_PORT", "5432")),
    )
