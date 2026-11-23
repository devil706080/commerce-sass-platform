from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from platform_control_plane.schemas.branding import ThemeKey


class TenantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=200)
    initial_owner_email: EmailStr
    storefront_display_name: str | None = Field(default=None, min_length=1, max_length=120)
    fallback_initials: str | None = Field(default=None, min_length=1, max_length=4)
    theme_key: ThemeKey = "ocean_teal"

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display name must not be blank")
        return value

    @field_validator("initial_owner_email")
    @classmethod
    def normalize_owner_email(cls, value: EmailStr) -> str:
        return str(value).strip().casefold()

    @field_validator("storefront_display_name")
    @classmethod
    def normalize_storefront_name(cls, value: str | None) -> str | None:
        return value.strip() if value else None

    @field_validator("fallback_initials")
    @classmethod
    def normalize_initials(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = "".join(
            character for character in value.upper() if character.isascii() and character.isalnum()
        )
        if not normalized:
            raise ValueError("initials must contain ASCII letters or numbers")
        return normalized[:4]


class TenantResponse(BaseModel):
    id: UUID
    display_name: str
    initial_owner_email: str | None
    status: Literal["PENDING", "PROVISIONING", "FAILED", "ACTIVE", "DELETION_REQUESTED"]
    created_at: datetime
    updated_at: datetime


class TenantOwnerContactUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    initial_owner_email: EmailStr

    @field_validator("initial_owner_email")
    @classmethod
    def normalize_owner_email(cls, value: EmailStr) -> str:
        return str(value).strip().casefold()
