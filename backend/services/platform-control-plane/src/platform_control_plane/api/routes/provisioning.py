from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session
from platform_control_plane.dependencies.operator import Operator, require_operator
from platform_control_plane.schemas.provisioning import (
    ProvisioningJobResponse,
    ProvisioningRequest,
    ServiceDatabaseResponse,
)

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}", dependencies=[Depends(require_operator)])
SessionDep = Annotated[Session, Depends(get_session)]
_JOB_FIELDS = (
    "id, tenant_id, service_key, status, attempt_count, error_code, "
    "created_at, updated_at, started_at, completed_at"
)
_DATABASE_FIELDS = (
    "id, tenant_id, service_key, tenant_database_id, schema_name, database_name, runtime_role, migrator_role, "
    "secret_reference, status, created_at, updated_at"
)


def _tenant_status(session: Session, tenant_id: UUID) -> str:
    value = session.execute(
        text("SELECT status FROM tenants WHERE id = :id"), {"id": tenant_id}
    ).scalar_one_or_none()
    if value is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return str(value)


def _require_verified_domain(session: Session, tenant_id: UUID) -> None:
    verified: bool = session.execute(
        text(
            "SELECT EXISTS (SELECT 1 FROM tenant_domains "
            "WHERE tenant_id = :tenant AND purpose = 'STOREFRONT' "
            "AND verification_status = 'VERIFIED')"
        ),
        {"tenant": tenant_id},
    ).scalar_one()
    if not verified:
        raise HTTPException(status_code=409, detail="Tenant requires a verified domain")


@router.post("/provisioning-jobs", response_model=ProvisioningJobResponse, status_code=201)
def request_provisioning(
    tenant_id: UUID,
    payload: ProvisioningRequest,
    response: Response,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    tenant_status = _tenant_status(session, tenant_id)
    if tenant_status not in {"PENDING", "PROVISIONING", "ACTIVE"}:
        raise HTTPException(status_code=409, detail="Tenant cannot be provisioned")
    _require_verified_domain(session, tenant_id)
    job = (
        session.execute(
            text(
                "INSERT INTO provisioning_jobs (id, tenant_id, service_key) "
                "VALUES (:id, :tenant, :service) "
                f"ON CONFLICT (tenant_id, service_key) DO NOTHING RETURNING {_JOB_FIELDS}"
            ),
            {"id": uuid4(), "tenant": tenant_id, "service": payload.service_key},
        )
        .mappings()
        .one_or_none()
    )
    if job is None:
        response.status_code = status.HTTP_200_OK
        return (
            session.execute(
                text(
                    f"SELECT {_JOB_FIELDS} FROM provisioning_jobs "
                    "WHERE tenant_id = :tenant AND service_key = :service"
                ),
                {"tenant": tenant_id, "service": payload.service_key},
            )
            .mappings()
            .one()
        )
    if tenant_status == "PENDING":
        session.execute(
            text("UPDATE tenants SET status = 'PROVISIONING', updated_at = now() WHERE id = :id"),
            {"id": tenant_id},
        )
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'PROVISIONING_REQUESTED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return job


@router.get("/provisioning-jobs", response_model=list[ProvisioningJobResponse])
def list_provisioning_jobs(tenant_id: UUID, session: SessionDep) -> Any:
    _tenant_status(session, tenant_id)
    return (
        session.execute(
            text(
                f"SELECT {_JOB_FIELDS} FROM provisioning_jobs "
                "WHERE tenant_id = :tenant ORDER BY created_at, id"
            ),
            {"tenant": tenant_id},
        )
        .mappings()
        .all()
    )


@router.post("/provisioning-jobs/{job_id}/retry", response_model=ProvisioningJobResponse)
def retry_provisioning(
    tenant_id: UUID,
    job_id: UUID,
    session: SessionDep,
    operator: Annotated[Operator, Depends(require_operator)],
) -> Any:
    if _tenant_status(session, tenant_id) not in {"PROVISIONING", "ACTIVE"}:
        raise HTTPException(status_code=409, detail="Tenant is not provisioning")
    job = (
        session.execute(
            text(
                "UPDATE provisioning_jobs SET status = 'PENDING', error_code = NULL, "
                "updated_at = now() WHERE id = :id AND tenant_id = :tenant AND status = 'FAILED' "
                f"RETURNING {_JOB_FIELDS}"
            ),
            {"id": job_id, "tenant": tenant_id},
        )
        .mappings()
        .one_or_none()
    )
    if job is None:
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    session.execute(
        text(
            "INSERT INTO tenant_audit_events (id, tenant_id, action, actor_issuer, actor_subject) "
            "VALUES (:audit, :tenant, 'PROVISIONING_RETRIED', :issuer, :subject)"
        ),
        {
            "audit": uuid4(),
            "tenant": tenant_id,
            "issuer": operator.issuer,
            "subject": operator.subject,
        },
    )
    session.commit()
    return job


@router.get("/service-databases", response_model=list[ServiceDatabaseResponse])
def list_service_databases(tenant_id: UUID, session: SessionDep) -> Any:
    _tenant_status(session, tenant_id)
    return (
        session.execute(
            text(
                f"SELECT {_DATABASE_FIELDS} FROM tenant_service_databases "
                "WHERE tenant_id = :tenant ORDER BY service_key"
            ),
            {"tenant": tenant_id},
        )
        .mappings()
        .all()
    )
