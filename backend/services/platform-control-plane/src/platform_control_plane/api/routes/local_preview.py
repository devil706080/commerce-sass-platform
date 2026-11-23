from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.core.themes import THEMES
from platform_control_plane.dependencies.database import get_session


class LocalPreview(BaseModel):
    tenant_id: UUID
    hostname: str
    purpose: Literal["STOREFRONT", "TENANT_ADMIN"]
    display_name: str
    tenant_status: Literal["PENDING", "PROVISIONING", "ACTIVE"]
    domain_status: Literal["VERIFIED"]
    notice: str = "Local preview only; not tenant authorization or database routing authority."


class LocalTenantAdminContext(BaseModel):
    tenant_id: UUID
    hostname: str
    purpose: Literal["STOREFRONT", "TENANT_ADMIN"]
    display_name: str
    fallback_initials: str
    theme_key: str
    palette: dict[str, str]
    tenant_status: Literal["ACTIVE"]
    domain_status: Literal["VERIFIED"]
    notice: str = "Local branding context only; it is not an authorization or database-routing authority."


router = APIRouter()


def _hostname(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-host", "").split(",", 1)[0].strip()
    return forwarded.split(":", 1)[0].lower() if forwarded else (request.url.hostname or "")


@router.get("/_local/tenant", response_model=LocalPreview, include_in_schema=False)
def local_preview(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> LocalPreview:
    if request.app.state.settings.app_environment != "local":
        raise HTTPException(status_code=404, detail="Not found")
    tenant = (
        session.execute(
            text(
                "SELECT t.id AS tenant_id, t.display_name, t.status AS tenant_status, "
                "d.hostname, d.purpose, d.verification_status AS domain_status "
                "FROM tenant_domains d JOIN tenants t ON t.id = d.tenant_id "
                "WHERE d.hostname = :hostname AND d.verification_status = 'VERIFIED' "
                "AND t.status IN ('PENDING', 'PROVISIONING', 'ACTIVE')"
            ),
            {"hostname": _hostname(request)},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Local tenant domain is not verified")
    return LocalPreview(**tenant)


@router.get("/_local/tenant-admin", response_model=LocalTenantAdminContext, include_in_schema=False)
def local_tenant_admin_context(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> LocalTenantAdminContext:
    settings = request.app.state.settings
    if settings.app_environment != "local":
        raise HTTPException(status_code=404, detail="Not found")
    tenant = (
        session.execute(
            text(
                "SELECT t.id AS tenant_id, b.display_name, b.fallback_initials, b.theme_key, "
                "t.status AS tenant_status, d.hostname, d.purpose, "
                "d.verification_status AS domain_status "
                "FROM tenant_domains d JOIN tenants t ON t.id = d.tenant_id "
                "JOIN tenant_branding b ON b.tenant_id = t.id "
                "WHERE d.hostname = :hostname AND d.verification_status = 'VERIFIED' "
                "AND d.purpose = 'TENANT_ADMIN' AND t.status = 'ACTIVE'"
            ),
            {"hostname": _hostname(request)},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Active tenant admin domain is not verified")
    context = dict(tenant)
    context["palette"] = dict(THEMES[context["theme_key"]])
    return LocalTenantAdminContext(**context)
