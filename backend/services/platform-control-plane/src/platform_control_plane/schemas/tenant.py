from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=200)

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display name must not be blank")
        return value


class TenantResponse(BaseModel):
    id: UUID
    display_name: str
    status: Literal["PENDING", "DELETION_REQUESTED"]
    created_at: datetime
    updated_at: datetime
