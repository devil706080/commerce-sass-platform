import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_HOSTNAME = re.compile(
    r"^(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


class DomainCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hostname: str = Field(min_length=1, max_length=253)
    purpose: Literal["STOREFRONT", "TENANT_ADMIN"] = "STOREFRONT"

    @field_validator("hostname")
    @classmethod
    def normalize_hostname(cls, value: str) -> str:
        value = value.strip().rstrip(".").lower()
        if "://" in value or "/" in value or ":" in value:
            raise ValueError("hostname must not include a scheme, path, or port")
        try:
            value = value.encode("idna").decode("ascii")
        except UnicodeError as error:
            raise ValueError("hostname is invalid") from error
        if not _HOSTNAME.fullmatch(value):
            raise ValueError("hostname is invalid")
        return value


class DomainResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    hostname: str
    purpose: Literal["STOREFRONT", "TENANT_ADMIN"]
    verification_status: Literal["PENDING_VERIFICATION", "VERIFIED"]
    verification_method: Literal["LOCAL"]
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
