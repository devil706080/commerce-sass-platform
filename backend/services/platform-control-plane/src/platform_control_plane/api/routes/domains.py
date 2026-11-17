from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session
from platform_control_plane.dependencies.operator import Operator, require_operator
from platform_control_plane.schemas.domain import DomainCreate, DomainResponse

router = APIRouter(
    prefix="/api/v1/tenants/{tenant_id}/domains",
    dependencies=[Depends(require_operator)],
)
SessionDep = Annotated[Session, Depends(get_session)]
_FIELDS = (
    "id, tenant_id, hostname, verification_status, verification_method, "
    "verified_at, created_at, updated_at"
)


def _require_local_adapter(request: Request) -> None:
    if request.app.state.settings.app_environment != "local":
        raise HTTPException(status_code=404, detail="Local domain adapter is disabled")


def _tenant_status(session: Session, tenant_id: UUID) -> str:
    status_value = session.execute(
        text("SELECT status FROM tenants WHERE id = :id"), {"id": tenant_id}
    ).scalar_one_or_none()
    if status_value is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return str(status_value)


def _require_onboardable_tenant(session: Session, tenant_id: UUID) -> None:
    if _tenant_status(session, tenant_id) != "PENDING":
        raise HTTPException(status_code=409, detail="Tenant cannot accept domain changes")


@router.post("", response_model=DomainResponse, status_code=201)
def register_domain(
    tenant_id: UUID,
    payload: DomainCreate,
    request: Request,
    response: Response,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    _require_local_adapter(request)
    if payload.hostname != "localhost" and not payload.hostname.endswith(".localhost"):
        raise HTTPException(status_code=422, detail="Local domains must use localhost")
    _require_onboardable_tenant(session, tenant_id)
    domain_id = uuid4()
    domain = (
        session.execute(
            text(
                "INSERT INTO tenant_domains (id, tenant_id, hostname) "
                "VALUES (:id, :tenant, :hostname) "
                f"ON CONFLICT (hostname) DO NOTHING RETURNING {_FIELDS}"
            ),
            {"id": domain_id, "tenant": tenant_id, "hostname": payload.hostname},
        )
        .mappings()
        .one_or_none()
    )
    if domain is None:
        existing = (
            session.execute(
                text(f"SELECT {_FIELDS} FROM tenant_domains WHERE hostname = :hostname"),
                {"hostname": payload.hostname},
            )
            .mappings()
            .one()
        )
        if existing.tenant_id != tenant_id:
            raise HTTPException(status_code=409, detail="Domain is already registered")
        response.status_code = status.HTTP_200_OK
        return existing
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'TENANT_DOMAIN_REGISTERED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return domain


@router.get("", response_model=list[DomainResponse])
def list_domains(
    tenant_id: UUID,
    request: Request,
    session: SessionDep,
) -> Any:
    _require_local_adapter(request)
    _tenant_status(session, tenant_id)
    return (
        session.execute(
            text(
                f"SELECT {_FIELDS} FROM tenant_domains "
                "WHERE tenant_id = :tenant ORDER BY created_at, id"
            ),
            {"tenant": tenant_id},
        )
        .mappings()
        .all()
    )


@router.post("/{domain_id}/verify", response_model=DomainResponse)
def verify_domain(
    tenant_id: UUID,
    domain_id: UUID,
    request: Request,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    _require_local_adapter(request)
    _require_onboardable_tenant(session, tenant_id)
    domain = (
        session.execute(
            text(
                f"SELECT {_FIELDS} FROM tenant_domains "
                "WHERE id = :id AND tenant_id = :tenant FOR UPDATE"
            ),
            {"id": domain_id, "tenant": tenant_id},
        )
        .mappings()
        .one_or_none()
    )
    if domain is None:
        raise HTTPException(status_code=404, detail="Domain not found")
    if domain.verification_status == "VERIFIED":
        return domain
    if domain.hostname not in request.app.state.settings.local_labels():
        raise HTTPException(status_code=409, detail="Local hostname is not configured")
    verified = (
        session.execute(
            text(
                "UPDATE tenant_domains SET verification_status = 'VERIFIED', "
                "verified_at = now(), updated_at = now() WHERE id = :id "
                f"RETURNING {_FIELDS}"
            ),
            {"id": domain_id},
        )
        .mappings()
        .one()
    )
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'TENANT_DOMAIN_VERIFIED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return verified
