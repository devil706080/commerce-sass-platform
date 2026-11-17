from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

ServiceKey = Literal["catalogue_fixture", "inventory_fixture"]


class ProvisioningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_key: ServiceKey


class ProvisioningJobResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    service_key: ServiceKey
    status: Literal["PENDING", "RUNNING", "INFRASTRUCTURE_READY", "FAILED"]
    attempt_count: int
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ServiceDatabaseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    service_key: ServiceKey
    tenant_database_id: UUID | None
    schema_name: str | None
    database_name: str
    runtime_role: str
    migrator_role: str
    secret_reference: str
    status: Literal["INFRASTRUCTURE_READY"]
    created_at: datetime
    updated_at: datetime
