from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from identity_access.api.schemas import InvitationCreate
from identity_access.application.service import IdentityService
from identity_access.domain.models import (
    AuthenticatedIdentity,
    Membership,
    MembershipStatus,
    StaffRole,
)


def identity(*roles: str, email: str = "admin@lifemac.test") -> AuthenticatedIdentity:
    return AuthenticatedIdentity("issuer", "subject", email, "Admin", roles)


class FakeRepository:
    def __init__(self, membership: Membership | None = None, bootstrap_allowed: bool = True):
        self.membership = membership
        self.bootstrap_allowed = bootstrap_allowed
        self.invitation: tuple[str, StaffRole] | None = None

    def create_invitation(self, email, role, actor):
        self.invitation = (email, role)
        return {
            "id": uuid4(),
            "email": email,
            "role": role,
            "status": "PENDING",
            "expires_at": None,
            "created_at": None,
            "accepted_at": None,
        }

    def accept_invitation(self, authenticated):
        return self.membership

    def find_membership(self, authenticated):
        return self.membership

    def list_memberships(self):
        return [self.membership] if self.membership else []

    def can_bootstrap_owner(self, email):
        return self.bootstrap_allowed

    def bootstrap_owner(self, authenticated):
        self.membership = membership()
        return self.membership


def membership(role=StaffRole.TENANT_OWNER, status=MembershipStatus.ACTIVE) -> Membership:
    return Membership(uuid4(), uuid4(), "admin@lifemac.test", "Admin", role, status)


def test_invitation_normalizes_email_and_rejects_invalid_input():
    request = InvitationCreate(email="  Admin@LIFEMAC.test ", role=StaffRole.TENANT_OWNER)
    assert request.email == "admin@lifemac.test"
    with pytest.raises(ValidationError):
        InvitationCreate(email="invalid")


def test_platform_operator_can_create_first_owner_invitation():
    repository = FakeRepository()
    service = IdentityService(repository)  # type: ignore[arg-type]
    service.invite("owner@lifemac.test", StaffRole.TENANT_OWNER, identity("platform-operator"))
    assert repository.invitation == ("owner@lifemac.test", StaffRole.TENANT_OWNER)


def test_platform_operator_cannot_manage_staff_or_create_a_second_owner_invitation():
    service = IdentityService(FakeRepository())  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as staff_error:
        service.invite("staff@lifemac.test", StaffRole.TENANT_ADMIN, identity("platform-operator"))
    assert staff_error.value.status_code == 403

    service = IdentityService(FakeRepository(bootstrap_allowed=False))  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as owner_error:
        service.invite("second@lifemac.test", StaffRole.TENANT_OWNER, identity("platform-operator"))
    assert owner_error.value.status_code == 403


def test_non_admin_membership_cannot_invite_staff():
    service = IdentityService(FakeRepository(membership(StaffRole.VIEWER)))  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as error:
        service.invite("staff@lifemac.test", StaffRole.VIEWER, identity("tenant-staff"))
    assert error.value.status_code == 403


def test_suspended_or_missing_membership_fails_closed():
    for stored in (None, membership(status=MembershipStatus.SUSPENDED)):
        service = IdentityService(FakeRepository(stored))  # type: ignore[arg-type]
        with pytest.raises(HTTPException) as error:
            service.require_active_membership(identity("tenant-admin"))
        assert error.value.status_code == 403


def test_invitation_acceptance_requires_a_matching_pending_invitation():
    service = IdentityService(FakeRepository())  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as error:
        service.accept(identity("tenant-admin"))
    assert error.value.status_code == 403


def test_exact_initial_owner_can_claim_membership_once():
    repository = FakeRepository()
    service = IdentityService(repository)  # type: ignore[arg-type]
    resolved = service.resolve_membership(
        identity("tenant-admin", email="owner@example.test"), "owner@example.test"
    )
    assert resolved.role == StaffRole.TENANT_OWNER


def test_different_email_cannot_claim_initial_owner_membership():
    service = IdentityService(FakeRepository())  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as error:
        service.resolve_membership(
            identity("tenant-admin", email="attacker@example.test"), "owner@example.test"
        )
    assert error.value.status_code == 403
