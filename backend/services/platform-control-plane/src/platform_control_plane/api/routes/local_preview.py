from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session


class LocalPreview(BaseModel):
    tenant_id: UUID
    hostname: str
    display_name: str
    tenant_status: Literal["PENDING"]
    domain_status: Literal["VERIFIED"]
    notice: str = "Local preview only; not tenant authorization or database routing authority."


router = APIRouter()


@router.get("/_local/tenant", response_model=LocalPreview, include_in_schema=False)
def local_preview(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> LocalPreview:
    settings = request.app.state.settings
    if settings.app_environment != "local":
        raise HTTPException(status_code=404, detail="Not found")
    hostname = request.url.hostname
    if (hostname or "") not in settings.local_labels():
        raise HTTPException(status_code=404, detail="Local tenant preview not configured")
    tenant = (
        session.execute(
            text(
                "SELECT t.id AS tenant_id, t.display_name, t.status AS tenant_status, "
                "d.hostname, d.verification_status AS domain_status "
                "FROM tenant_domains d JOIN tenants t ON t.id = d.tenant_id "
                "WHERE d.hostname = :hostname AND d.verification_status = 'VERIFIED' "
                "AND t.status = 'PENDING'"
            ),
            {"hostname": hostname},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Local tenant domain is not verified")
    return LocalPreview(**tenant)
