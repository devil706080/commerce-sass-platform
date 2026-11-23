from typing import Annotated

from fastapi import APIRouter, Depends, Request

from identity_access.api.schemas import (
    InvitationCreate,
    InvitationResponse,
    MembershipResponse,
    MeResponse,
)
from identity_access.application.service import IdentityService
from identity_access.dependencies.auth import require_identity
from identity_access.dependencies.tenant import require_tenant_host
from identity_access.domain.models import AuthenticatedIdentity
from identity_access.infrastructure.repository import IdentityRepository

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_tenant_host)])
IdentityDep = Annotated[AuthenticatedIdentity, Depends(require_identity)]


def service(request: Request) -> IdentityService:
    return IdentityService(IdentityRepository(request.state.tenant_settings))


@router.post("/staff/invitations", response_model=InvitationResponse, status_code=201)
def create_invitation(
    payload: InvitationCreate,
    identity: IdentityDep,
    application: Annotated[IdentityService, Depends(service)],
) -> dict[str, object]:
    return application.invite(payload.email, payload.role, identity)


@router.post("/staff/invitations/accept", response_model=MeResponse)
def accept_invitation(
    request: Request,
    identity: IdentityDep,
    application: Annotated[IdentityService, Depends(service)],
) -> MeResponse:
    membership = application.accept(identity)
    return MeResponse(
        tenant_id=request.state.tenant_settings.tenant_id,
        membership=MembershipResponse.model_validate(membership, from_attributes=True),
    )


@router.get("/me", response_model=MeResponse)
def me(
    request: Request,
    identity: IdentityDep,
    application: Annotated[IdentityService, Depends(service)],
) -> MeResponse:
    membership = application.resolve_membership(
        identity, request.state.tenant_settings.initial_owner_email
    )
    return MeResponse(
        tenant_id=request.state.tenant_settings.tenant_id,
        membership=MembershipResponse.model_validate(membership, from_attributes=True),
    )


@router.get("/staff", response_model=list[MembershipResponse])
def list_staff(
    identity: IdentityDep,
    application: Annotated[IdentityService, Depends(service)],
) -> list[MembershipResponse]:
    return [
        MembershipResponse.model_validate(item, from_attributes=True)
        for item in application.list_staff(identity)
    ]
