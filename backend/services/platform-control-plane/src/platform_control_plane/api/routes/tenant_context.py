import hmac
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session

router = APIRouter(prefix="/_internal", include_in_schema=False)
SessionDep = Annotated[Session, Depends(get_session)]

ServiceKey = Literal["identity_access", "catalogue_fixture", "media_fixture"]
AUDIENCES: dict[ServiceKey, str] = {
    "identity_access": "identity-api",
    "catalogue_fixture": "catalogue-api",
    "media_fixture": "media-api",
}


class TenantContextResponse(BaseModel):
    token: str
    expires_in: int = 60


class TenantAdminDomainsResponse(BaseModel):
    hostnames: list[str]


def _secret(request: Request, name: str) -> str:
    value = getattr(request.app.state.settings, name)
    if value is None or not value.get_secret_value():
        raise HTTPException(status_code=503, detail="Tenant context service is unavailable")
    return value.get_secret_value()


def _require_broker(request: Request, authorization: str | None) -> None:
    expected = _secret(request, "tenant_context_broker_token")
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Internal authentication required")


@router.get("/tenant-admin-domains", response_model=TenantAdminDomainsResponse)
def tenant_admin_domains(
    request: Request,
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> TenantAdminDomainsResponse:
    _require_broker(request, authorization)
    hostnames = session.execute(
        text(
            "SELECT d.hostname FROM tenant_domains d "
            "JOIN tenants t ON t.id=d.tenant_id "
            "WHERE d.purpose='TENANT_ADMIN' AND d.verification_status='VERIFIED' "
            "AND t.status='ACTIVE' ORDER BY d.hostname"
        )
    ).scalars().all()
    return TenantAdminDomainsResponse(hostnames=list(hostnames))


@router.post("/tenant-context", response_model=TenantContextResponse)
def issue_tenant_context(
    service_key: ServiceKey,
    request: Request,
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
    forwarded_host: Annotated[str | None, Header(alias="X-Forwarded-Host")] = None,
) -> TenantContextResponse:
    _require_broker(request, authorization)
    hostname = (forwarded_host or "").split(",", 1)[0].split(":", 1)[0].strip().lower().rstrip(".")
    if not hostname:
        raise HTTPException(status_code=400, detail="Tenant hostname is required")
    row = (
        session.execute(
            text(
                "SELECT t.id AS tenant_id,t.initial_owner_email,d.hostname,s.database_name,s.schema_name,"
                "s.runtime_role,s.secret_reference FROM tenant_domains d "
                "JOIN tenants t ON t.id=d.tenant_id "
                "JOIN tenant_service_databases s ON s.tenant_id=t.id AND s.service_key=:service "
                "JOIN tenant_service_readiness r ON r.tenant_id=t.id AND r.service_key=:service "
                "WHERE d.hostname=:hostname AND d.purpose='TENANT_ADMIN' "
                "AND d.verification_status='VERIFIED' AND t.status='ACTIVE' "
                "AND s.status='INFRASTRUCTURE_READY' AND r.migration_status='MIGRATED' "
                "AND r.smoke_status='PASSED'"
            ),
            {"hostname": hostname, "service": service_key},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Active tenant service context not found")
    now = datetime.now(UTC)
    context = dict(row)
    context["tenant_id"] = str(context["tenant_id"])
    owner_email = context.pop("initial_owner_email", None)
    claims = {
        **context,
        "iss": "platform-control-plane",
        "aud": AUDIENCES[service_key],
        "iat": now,
        "exp": now + timedelta(seconds=60),
    }
    if service_key == "identity_access" and owner_email:
        claims["initial_owner_email"] = owner_email
    token = jwt.encode(claims, _secret(request, "tenant_context_signing_secret"), algorithm="HS256")
    return TenantContextResponse(token=token)
