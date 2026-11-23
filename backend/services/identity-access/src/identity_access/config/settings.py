import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus
from uuid import UUID


@dataclass(frozen=True)
class Settings:
    tenant_id: UUID | None = None
    allowed_hosts: frozenset[str] = frozenset()
    database_name: str | None = None
    runtime_role: str | None = None
    migrator_role: str | None = None
    secret_file: Path | None = None
    db_host: str = "postgres"
    db_port: int = 5432
    schema_name: str = "identity"
    oidc_issuer: str = ""
    oidc_audience: str = "identity-api"
    oidc_jwks_url: str = ""
    cors_origins: tuple[str, ...] = ()
    tenant_context_signing_secret: str = ""
    provisioned_secrets_dir: Path = Path("/var/lib/platform-secrets")
    initial_owner_email: str | None = None

    def database_url(self, credential: str = "runtime_password") -> str:
        if not self.secret_file or not self.database_name or not self.runtime_role:
            raise ValueError("identity tenant database configuration is unavailable")
        payload = json.loads(self.secret_file.read_text(encoding="utf-8"))
        if credential not in {"runtime_password", "migrator_password"}:
            raise ValueError("unsupported database credential")
        password = payload.get(credential)
        if not isinstance(password, str) or not password:
            raise ValueError("identity database credential is unavailable")
        role = self.runtime_role if credential == "runtime_password" else self.migrator_role
        if not role:
            raise ValueError("identity database role is unavailable")
        return f"postgresql://{quote_plus(role)}:{quote_plus(password)}@{self.db_host}:{self.db_port}/{self.database_name}"


def load_settings() -> Settings:
    allowed_hosts_value = os.getenv("IDENTITY_ALLOWED_HOSTS", "").strip()
    allowed_hosts = (
        json.loads(allowed_hosts_value)
        if allowed_hosts_value.startswith("[")
        else allowed_hosts_value.split(",")
    )
    normalized_hosts = frozenset(
        str(host).strip().lower().rstrip(".") for host in allowed_hosts if str(host).strip()
    )
    cors_origins_value = json.loads(os.getenv("IDENTITY_CORS_ORIGINS", "[]"))
    if not isinstance(cors_origins_value, list) or not all(
        isinstance(origin, str) for origin in cors_origins_value
    ):
        raise ValueError("IDENTITY_CORS_ORIGINS must be a JSON string array")
    return Settings(
        tenant_id=UUID(os.environ["IDENTITY_TENANT_ID"]) if os.getenv("IDENTITY_TENANT_ID") else None,
        allowed_hosts=normalized_hosts,
        database_name=os.getenv("IDENTITY_DATABASE_NAME"),
        runtime_role=os.getenv("IDENTITY_RUNTIME_ROLE"),
        migrator_role=os.getenv("IDENTITY_MIGRATOR_ROLE"),
        secret_file=Path(os.environ["IDENTITY_SECRET_FILE"]) if os.getenv("IDENTITY_SECRET_FILE") else None,
        db_host=os.getenv("IDENTITY_DB_HOST", "postgres"),
        db_port=int(os.getenv("IDENTITY_DB_PORT", "5432")),
        schema_name=os.getenv("IDENTITY_SCHEMA", "identity"),
        oidc_issuer=os.environ["IDENTITY_OIDC_ISSUER"],
        oidc_audience=os.getenv("IDENTITY_OIDC_AUDIENCE", "identity-api"),
        oidc_jwks_url=os.environ["IDENTITY_OIDC_JWKS_URL"],
        cors_origins=tuple(origin.rstrip("/") for origin in cors_origins_value),
        tenant_context_signing_secret=os.getenv("TENANT_CONTEXT_SIGNING_SECRET", ""),
        provisioned_secrets_dir=Path(os.getenv("PROVISIONED_SECRETS_DIR", "/var/lib/platform-secrets")),
    )
