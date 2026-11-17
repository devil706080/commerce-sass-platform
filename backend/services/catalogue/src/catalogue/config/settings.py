import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

@dataclass(frozen=True)
class Settings:
    database_url: str | None
    schema_name: str
    tenant_hosts: dict[str, str]
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""

def load_settings() -> Settings:
    database_url = os.getenv("CATALOGUE_DATABASE_URL")
    secret_file = os.getenv("CATALOGUE_SECRET_FILE")
    if not database_url and secret_file:
        payload = json.loads(Path(secret_file).read_text(encoding="utf-8"))
        database_url = "postgresql://{}:{}@{}:{}/{}".format(
            quote_plus(os.environ["CATALOGUE_RUNTIME_ROLE"]),
            quote_plus(payload["runtime_password"]),
            os.getenv("CATALOGUE_DB_HOST", "postgres"),
            os.getenv("CATALOGUE_DB_PORT", "5432"),
            os.environ["CATALOGUE_DATABASE_NAME"],
        )
    return Settings(database_url, os.getenv("CATALOGUE_SCHEMA", "catfx"), json.loads(os.getenv("TENANT_HOSTS", "{}")), os.getenv("CATALOGUE_OIDC_ISSUER", ""), os.getenv("CATALOGUE_OIDC_AUDIENCE", ""), os.getenv("CATALOGUE_OIDC_JWKS_URL", ""))
