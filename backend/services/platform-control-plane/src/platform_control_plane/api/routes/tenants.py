import hashlib
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session
from platform_control_plane.dependencies.operator import Operator, require_operator
from platform_control_plane.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter(prefix="/api/v1/tenants", dependencies=[Depends(require_operator)])
SessionDep = Annotated[Session, Depends(get_session)]
_FIELDS = "id, display_name, status, created_at, updated_at"


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
                "INSERT INTO tenants (id, display_name) VALUES (:id, :name) "
                f"ON CONFLICT (lower(btrim(display_name))) DO NOTHING RETURNING {_FIELDS}"
            ),
            {"id": tenant_id, "name": payload.display_name},
        )
        .mappings()
        .one_or_none()
    )
    if tenant is None:
        raise HTTPException(status_code=409, detail="A tenant with this name already exists")
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
