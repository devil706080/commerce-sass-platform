import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr, ValidationError

from platform_control_plane.core.config import RuntimeSettings, WorkerSettings
from platform_control_plane.schemas.provisioning import ProvisioningRequest
from platform_control_plane.worker.provisioner import database_identity, load_or_create_secrets
from platform_control_plane.worker.service_migrations import (
    CATALOGUE_PRODUCT_RUNTIME_PRIVILEGES,
    OWNED_SERVICE_KEYS,
)


def test_database_identity_is_opaque_stable_and_service_scoped() -> None:
    tenant_id = UUID("49e84243-f9e4-4981-b3a5-38f943cc79ba")
    catalogue = database_identity(tenant_id, "catalogue_fixture")
    inventory = database_identity(tenant_id, "inventory_fixture")
    identity = database_identity(tenant_id, "identity_access")

    assert catalogue == database_identity(tenant_id, "catalogue_fixture")
    assert catalogue.database_name == inventory.database_name
    assert catalogue.schema_name != inventory.schema_name
    assert identity.schema_name == "identity"
    assert identity.database_name == catalogue.database_name
    assert identity.runtime_role.endswith("_identity_rt")
    assert identity.migrator_role.endswith("_identity_mg")
    assert "lifemac" not in catalogue.database_name
    assert max(map(len, catalogue.__dict__.values())) <= 63


def test_database_identity_rejects_unknown_service() -> None:
    with pytest.raises(ValueError, match="unsupported service"):
        database_identity(uuid4(), "orders")


def test_identity_access_is_a_supported_provisioning_contract() -> None:
    request = ProvisioningRequest(service_key="identity_access")
    assert request.service_key == "identity_access"
    with pytest.raises(ValidationError):
        ProvisioningRequest(service_key="identity-admin")  # type: ignore[arg-type]


def test_tenant_service_migration_runner_covers_every_provisioned_schema() -> None:
    assert set(OWNED_SERVICE_KEYS) == {
        "catalogue_fixture",
        "identity_access",
        "inventory_fixture",
        "media_fixture",
    }


def test_catalogue_runtime_can_complete_product_crud() -> None:
    assert CATALOGUE_PRODUCT_RUNTIME_PRIVILEGES == "SELECT, INSERT, UPDATE, DELETE"


def test_local_secret_is_idempotent_and_file_is_not_world_readable(tmp_path: Path) -> None:
    job_id = uuid4()
    first = load_or_create_secrets(str(tmp_path), job_id)
    second = load_or_create_secrets(str(tmp_path), job_id)

    assert first == second
    assert first.runtime_password != first.migrator_password
    assert first.reference == f"local-volume://{job_id}.json"
    if os.name != "nt":
        mode = (tmp_path / f"{job_id}.json").stat().st_mode
        assert mode & 0o040 != 0  # deployment-selected reader group
        assert mode & 0o007 == 0  # never world-readable
    payload = json.loads((tmp_path / f"{job_id}.json").read_text(encoding="utf-8"))
    assert set(payload) == {"runtime_password", "migrator_password"}


def test_api_runtime_settings_do_not_accept_worker_credentials() -> None:
    runtime_fields = RuntimeSettings.model_fields
    worker_fields = WorkerSettings.model_fields

    assert "platform_control_worker_password" not in runtime_fields
    assert "tenant_database_provisioner_password" not in runtime_fields
    assert "platform_control_worker_password" in worker_fields
    assert "tenant_database_provisioner_password" in worker_fields


def test_worker_urls_use_distinct_roles() -> None:
    settings = WorkerSettings(
        db_host="postgres",
        platform_control_worker_password=SecretStr("worker-test"),
        tenant_database_provisioner_password=SecretStr("provisioner-test"),
    )

    assert settings.worker_database_url().username == "platform_control_worker"
    assert settings.worker_database_url().database == "platform_control"
    assert settings.provisioner_database_url().username == "tenant_database_provisioner"
    assert settings.provisioner_database_url().database == "postgres"
