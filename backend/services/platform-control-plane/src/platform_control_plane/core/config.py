from pydantic import Field, SecretStr
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
    db_pool_size: int = Field(default=5, ge=1, le=10)
    db_max_overflow: int = Field(default=0, ge=0, le=5)
    db_pool_timeout: int = Field(default=5, ge=1, le=30)

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
