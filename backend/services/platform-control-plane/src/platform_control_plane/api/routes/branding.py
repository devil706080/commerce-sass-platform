from typing import Annotated, Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.core.themes import THEMES
from platform_control_plane.dependencies.database import get_session
from platform_control_plane.dependencies.operator import Operator, require_operator
from platform_control_plane.schemas.branding import (
    BrandingInput,
    BrandingResponse,
    ThemeKey,
    ThemeResponse,
    generated_initials,
    palette,
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_operator)])
SessionDep = Annotated[Session, Depends(get_session)]
_FIELDS = (
    "tenant_id, display_name, fallback_initials, theme_key, logo_media_id, created_at, updated_at"
)


def _response(row: Any) -> BrandingResponse:
    data = dict(row)
    data["palette"] = palette(data["theme_key"])
    return BrandingResponse(**data)


@router.get("/themes", response_model=list[ThemeResponse])
def list_themes() -> list[ThemeResponse]:
    return [
        ThemeResponse(
            key=cast(ThemeKey, key),
            name=value["name"],
            primary=value["primary"],
            primary_dark=value["primary_dark"],
            accent=value["accent"],
            surface=value["surface"],
        )
        for key, value in THEMES.items()
    ]


@router.get("/tenants/{tenant_id}/branding", response_model=BrandingResponse)
def get_branding(tenant_id: UUID, session: SessionDep) -> BrandingResponse:
    row = (
        session.execute(
            text(f"SELECT {_FIELDS} FROM tenant_branding WHERE tenant_id = :tenant"),
            {"tenant": tenant_id},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Tenant branding not found")
    return _response(row)


@router.put("/tenants/{tenant_id}/branding", response_model=BrandingResponse)
def update_branding(
    tenant_id: UUID,
    payload: BrandingInput,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> BrandingResponse:
    initials = payload.fallback_initials or generated_initials(payload.display_name)
    row = (
        session.execute(
            text(
                "UPDATE tenant_branding "
                "SET display_name = :name, fallback_initials = :initials, "
                "theme_key = :theme, updated_at = now() "
                "WHERE tenant_id = :tenant "
                f"RETURNING {_FIELDS}"
            ),
            {
                "tenant": tenant_id,
                "name": payload.display_name,
                "initials": initials,
                "theme": payload.theme_key,
            },
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Tenant branding not found")

    session.execute(
        text(
            "INSERT INTO tenant_audit_events "
            "(id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:id, :tenant, 'TENANT_BRANDING_UPDATED', :issuer, :subject)"
        ),
        {
            "id": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return _response(row)
