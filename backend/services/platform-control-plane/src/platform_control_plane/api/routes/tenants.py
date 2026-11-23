import hashlib
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session
from platform_control_plane.dependencies.operator import Operator, require_operator
from platform_control_plane.schemas.branding import generated_initials
from platform_control_plane.schemas.tenant import (
    TenantCreate,
    TenantOwnerContactUpdate,
    TenantResponse,
)

router = APIRouter(prefix="/api/v1/tenants", dependencies=[Depends(require_operator)])
SessionDep = Annotated[Session, Depends(get_session)]
_FIELDS = "id, display_name, initial_owner_email, status, created_at, updated_at"


@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant(
    payload: TenantCreate,
    response: Response,
    session: SessionDep,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    digest = hashlib.sha256(payload.model_dump_json().encode("utf-8")).hexdigest()
    # Serialize the same key without persisting a separate lock or leaking the key to logs.
    session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})
    previous = session.execute(
        text(
            "SELECT request_hash, tenant_id FROM tenant_create_idempotency WHERE request_key = :key"
        ),
        {"key": key},
    ).one_or_none()
    if previous:
        if previous.request_hash != digest:
            raise HTTPException(status_code=409, detail="Idempotency key already used")
        response.status_code = status.HTTP_200_OK
        return (
            session.execute(
                text(f"SELECT {_FIELDS} FROM tenants WHERE id = :id"), {"id": previous.tenant_id}
            )
            .mappings()
            .one()
        )
    tenant_id = uuid4()
    tenant = (
        session.execute(
            text(
                "INSERT INTO tenants (id, display_name, initial_owner_email) "
                "VALUES (:id, :name, :owner_email) "
                f"ON CONFLICT (lower(btrim(display_name))) DO NOTHING RETURNING {_FIELDS}"
            ),
            {
                "id": tenant_id,
                "name": payload.display_name,
                "owner_email": str(payload.initial_owner_email),
            },
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=409, detail="A tenant with this name already exists")
    branding_name = payload.storefront_display_name or payload.display_name
    session.execute(
        text(
            "INSERT INTO tenant_branding "
            "(tenant_id, display_name, fallback_initials, theme_key) "
            "VALUES (:tenant, :name, :initials, :theme)"
        ),
        {
            "tenant": tenant_id,
            "name": branding_name,
            "initials": payload.fallback_initials or generated_initials(branding_name),
            "theme": payload.theme_key,
        },
    )
    session.execute(
        text(
            "INSERT INTO tenant_create_idempotency (request_key, request_hash, tenant_id) "
            "VALUES (:key, :digest, :id)"
        ),
        {"key": key, "digest": digest, "id": tenant_id},
    )
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'TENANT_CREATED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return tenant


@router.get("", response_model=list[TenantResponse])
def list_tenants(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> Any:
    return (
        session.execute(
            text(
                f"SELECT {_FIELDS} FROM tenants ORDER BY created_at, id LIMIT :limit OFFSET :offset"
            ),
            {"limit": limit, "offset": offset},
        )
        .mappings()
        .all()
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: UUID, session: SessionDep) -> Any:
    tenant = (
        session.execute(text(f"SELECT {_FIELDS} FROM tenants WHERE id = :id"), {"id": tenant_id})
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}/owner-contact", response_model=TenantResponse)
def update_owner_contact(
    tenant_id: UUID,
    payload: TenantOwnerContactUpdate,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    tenant = (
        session.execute(
            text(
                "UPDATE tenants SET initial_owner_email=:owner_email, updated_at=now() "
                f"WHERE id=:id AND status <> 'DELETION_REQUESTED' RETURNING {_FIELDS}"
            ),
            {"id": tenant_id, "owner_email": str(payload.initial_owner_email)},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found or unavailable")
    session.execute(
        text(
            "INSERT INTO tenant_audit_events "
            "(id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'TENANT_OWNER_CONTACT_UPDATED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return tenant


@router.delete("/{tenant_id}", response_model=TenantResponse)
def request_tenant_deletion(
    tenant_id: UUID,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    tenant = (
        session.execute(
            text(
                "UPDATE tenants SET status = 'DELETION_REQUESTED', updated_at = now() "
                "WHERE id = :id AND status = 'PENDING' "
                f"RETURNING {_FIELDS}"
            ),
            {"id": tenant_id},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        existing = (
            session.execute(
                text(f"SELECT {_FIELDS} FROM tenants WHERE id = :id"), {"id": tenant_id}
            )
            .mappings()
            .one_or_none()
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return existing
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'TENANT_DELETION_REQUESTED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return tenant


@router.post("/{tenant_id}/activate", response_model=TenantResponse)
def activate_tenant(
    tenant_id: UUID,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    ready: bool = session.execute(
        text(
            "SELECT count(*) > 0 AND bool_and(migration_status = 'MIGRATED' "
            "AND smoke_status = 'PASSED') FROM tenant_service_readiness WHERE tenant_id = :id"
        ),
        {"id": tenant_id},
    ).scalar_one()
    if not ready:
        raise HTTPException(status_code=409, detail="Tenant services are not fully ready")
    tenant = (
        session.execute(
            text(
                "UPDATE tenants SET status='ACTIVE', updated_at=now() WHERE id=:id AND status='PROVISIONING' RETURNING "
                + _FIELDS
            ),
            {"id": tenant_id},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=409, detail="Tenant is not ready for activation")
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) VALUES (:audit,:tenant,'TENANT_ACTIVATED',:issuer,:subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return tenant
