import json
import re
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    db_host: str = Field(min_length=1)
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(default="platform_control", min_length=1)
    db_connect_timeout: int = Field(default=5, ge=1, le=30)

    def make_url(self, username: str, password: SecretStr) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=username,
            password=password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


class RuntimeSettings(DatabaseSettings):
    platform_control_runtime_password: SecretStr
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    cors_allowed_origins: str = ""
    app_environment: Literal["local", "production"] = "production"
    local_tenant_labels: str = ""
    db_pool_size: int = Field(default=5, ge=1, le=10)
    db_max_overflow: int = Field(default=0, ge=0, le=5)
    db_pool_timeout: int = Field(default=5, ge=1, le=30)

    def local_labels(self) -> dict[str, str]:
        if not self.local_tenant_labels:
            return {}
        try:
            labels = json.loads(self.local_tenant_labels)
        except json.JSONDecodeError as exc:
            raise ValueError("LOCAL_TENANT_LABELS must be a JSON object") from exc
        if not isinstance(labels, dict) or len(labels) > 50:
            raise ValueError("LOCAL_TENANT_LABELS must contain at most 50 hostnames")
        result: dict[str, str] = {}
        for host, name in labels.items():
            if (
                not isinstance(host, str)
                or len(host) > 253
                or not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*localhost", host)
                or not isinstance(name, str)
                or not name.strip()
                or len(name) > 200
            ):
                raise ValueError(
                    "Local labels require lowercase .localhost hosts and non-empty names"
                )
            result[host] = name.strip()
        return result

    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_local_labels(self) -> Self:
        if self.app_environment != "local" and self.local_tenant_labels:
            raise ValueError("LOCAL_TENANT_LABELS are permitted only in local mode")
        self.local_labels()
        return self

    def database_url(self) -> URL:
        if not self.platform_control_runtime_password.get_secret_value():
            raise ValueError("runtime password must not be empty")
        return self.make_url("platform_control_runtime", self.platform_control_runtime_password)


class MigrationSettings(DatabaseSettings):
    platform_control_migrator_password: SecretStr

    def database_url(self) -> URL:
        if not self.platform_control_migrator_password.get_secret_value():
            raise ValueError("migrator password must not be empty")
        return self.make_url("platform_control_migrator", self.platform_control_migrator_password)
