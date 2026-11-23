from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from identity_access.domain.models import MembershipStatus, StaffRole


class InvitationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=320)
    role: StaffRole = StaffRole.TENANT_ADMIN

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized.count("@") != 1 or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("valid email address is required")
        return normalized


class InvitationResponse(BaseModel):
    id: UUID
    email: str
    role: StaffRole
    status: str
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None


class MembershipResponse(BaseModel):
    id: UUID
    principal_id: UUID
    email: str
    display_name: str | None
    role: StaffRole
    status: MembershipStatus


class MeResponse(BaseModel):
    tenant_id: UUID
    membership: MembershipResponse
