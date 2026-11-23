from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class StaffRole(StrEnum):
    TENANT_OWNER = "TENANT_OWNER"
    TENANT_ADMIN = "TENANT_ADMIN"
    CATALOGUE_MANAGER = "CATALOGUE_MANAGER"
    ORDER_MANAGER = "ORDER_MANAGER"
    VIEWER = "VIEWER"


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class AuthenticatedIdentity:
    issuer: str
    subject: str
    email: str
    display_name: str | None
    realm_roles: tuple[str, ...]


@dataclass(frozen=True)
class Membership:
    id: UUID
    principal_id: UUID
    email: str
    display_name: str | None
    role: StaffRole
    status: MembershipStatus
