from fastapi import HTTPException

from identity_access.domain.models import (
    AuthenticatedIdentity,
    Membership,
    MembershipStatus,
    StaffRole,
)
from identity_access.infrastructure.repository import IdentityRepository, OwnerBootstrapConflict


class IdentityService:
    def __init__(self, repository: IdentityRepository):
        self.repository = repository

    def invite(
        self, email: str, role: StaffRole, actor: AuthenticatedIdentity
    ) -> dict[str, object]:
        if "platform-operator" in actor.realm_roles:
            if role != StaffRole.TENANT_OWNER or not self.repository.can_bootstrap_owner(email):
                raise HTTPException(
                    status_code=403,
                    detail="Platform operators may only bootstrap the first tenant owner",
                )
            try:
                return self.repository.create_invitation(email, role, actor)
            except OwnerBootstrapConflict:
                raise HTTPException(
                    status_code=403,
                    detail="Platform operators may only bootstrap the first tenant owner",
                ) from None
        membership = self.require_active_membership(actor)
        if membership.role not in {StaffRole.TENANT_OWNER, StaffRole.TENANT_ADMIN}:
            raise HTTPException(status_code=403, detail="Permission denied")
        if role == StaffRole.TENANT_OWNER and membership.role != StaffRole.TENANT_OWNER:
            raise HTTPException(status_code=403, detail="Only an owner can invite another owner")
        return self.repository.create_invitation(email, role, actor)

    def accept(self, identity: AuthenticatedIdentity) -> Membership:
        membership = self.repository.accept_invitation(identity)
        if membership is None:
            raise HTTPException(status_code=403, detail="No active invitation for this account")
        return membership

    def require_active_membership(self, identity: AuthenticatedIdentity) -> Membership:
        membership = self.repository.find_membership(identity)
        if membership is None or membership.status != MembershipStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Tenant membership unavailable")
        return membership

    def resolve_membership(
        self, identity: AuthenticatedIdentity, initial_owner_email: str | None
    ) -> Membership:
        membership = self.repository.find_membership(identity)
        if membership is not None and membership.status == MembershipStatus.ACTIVE:
            return membership
        if (
            initial_owner_email
            and identity.email == initial_owner_email.casefold()
            and "tenant-admin" in identity.realm_roles
        ):
            try:
                return self.repository.bootstrap_owner(identity)
            except OwnerBootstrapConflict:
                raise HTTPException(
                    status_code=403, detail="Tenant membership unavailable"
                ) from None
        raise HTTPException(status_code=403, detail="Tenant membership unavailable")

    def list_staff(self, identity: AuthenticatedIdentity) -> list[Membership]:
        membership = self.require_active_membership(identity)
        if membership.role not in {StaffRole.TENANT_OWNER, StaffRole.TENANT_ADMIN}:
            raise HTTPException(status_code=403, detail="Permission denied")
        return self.repository.list_memberships()
