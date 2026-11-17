import json
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from platform_control_plane.core.config import RuntimeSettings
from platform_control_plane.database.engine import create_runtime_engine
from platform_control_plane.dependencies.database import get_session
from platform_control_plane.dependencies.operator import Operator, require_operator
from platform_control_plane.main import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("RUN_DB_INTEGRATION"),
        reason="requires local PostgreSQL and approved migration",
    ),
]


def test_registry_create_idempotency_and_reads():
    engine = create_runtime_engine(RuntimeSettings())
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        app = create_app()
        app.dependency_overrides[require_operator] = lambda: Operator(
            "test-issuer", "test-operator"
        )
        app.dependency_overrides[get_session] = lambda: session
        key = str(uuid4())
        with TestClient(app) as client:
            first = client.post(
                "/api/v1/tenants",
                json={"display_name": "  Example tenant  "},
                headers={"Idempotency-Key": key},
            )
            assert first.status_code == 201
            tenant = first.json()
            assert tenant["display_name"] == "Example tenant"
            assert tenant["status"] == "PENDING"
            repeat = client.post(
                "/api/v1/tenants",
                json={"display_name": "Example tenant"},
                headers={"Idempotency-Key": key},
            )
            assert repeat.status_code == 200
            assert repeat.json()["id"] == tenant["id"]
            conflict = client.post(
                "/api/v1/tenants",
                json={"display_name": "Different"},
                headers={"Idempotency-Key": key},
            )
            assert conflict.status_code == 409
            duplicate = client.post(
                "/api/v1/tenants",
                json={"display_name": " example TENANT "},
                headers={"Idempotency-Key": str(uuid4())},
            )
            assert duplicate.status_code == 409
            assert duplicate.json() == {"detail": "A tenant with this name already exists"}
            assert client.get(f"/api/v1/tenants/{tenant['id']}").json() == tenant
            assert client.get("/api/v1/tenants?limit=101").status_code == 422
            assert any(t["id"] == tenant["id"] for t in client.get("/api/v1/tenants").json())
            deletion = client.delete(f"/api/v1/tenants/{tenant['id']}")
            assert deletion.status_code == 200
            assert deletion.json()["status"] == "DELETION_REQUESTED"
            repeated_deletion = client.delete(f"/api/v1/tenants/{tenant['id']}")
            assert repeated_deletion.status_code == 200
            assert repeated_deletion.json()["status"] == "DELETION_REQUESTED"
        session.close()
        transaction.rollback()
    engine.dispose()


def test_local_domain_registration_and_verification(monkeypatch):
    host = f"tenant-{uuid4().hex}.localhost"
    unconfigured_host = f"unconfigured-{uuid4().hex}.localhost"
    monkeypatch.setenv("APP_ENVIRONMENT", "local")
    monkeypatch.setenv("LOCAL_TENANT_LABELS", json.dumps({host: "Domain Test"}))
    engine = create_runtime_engine(RuntimeSettings())
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        app = create_app()
        app.dependency_overrides[require_operator] = lambda: Operator(
            "test-issuer", "test-operator"
        )
        app.dependency_overrides[get_session] = lambda: session
        with TestClient(app) as client:
            first_tenant = client.post(
                "/api/v1/tenants",
                json={"display_name": f"Domain Test {uuid4().hex}"},
                headers={"Idempotency-Key": str(uuid4())},
            ).json()
            second_tenant = client.post(
                "/api/v1/tenants",
                json={"display_name": f"Domain Conflict {uuid4().hex}"},
                headers={"Idempotency-Key": str(uuid4())},
            ).json()
            registered = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains",
                json={"hostname": host.upper() + "."},
            )
            assert registered.status_code == 201
            domain = registered.json()
            assert domain["hostname"] == host
            assert domain["verification_status"] == "PENDING_VERIFICATION"
            repeat = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains",
                json={"hostname": host},
            )
            assert repeat.status_code == 200
            assert repeat.json()["id"] == domain["id"]
            conflict = client.post(
                f"/api/v1/tenants/{second_tenant['id']}/domains",
                json={"hostname": host},
            )
            assert conflict.status_code == 409
            assert (
                client.post(
                    f"/api/v1/tenants/{first_tenant['id']}/domains",
                    json={"hostname": "example.com"},
                ).status_code
                == 422
            )
            unconfigured = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains",
                json={"hostname": unconfigured_host},
            ).json()
            failed_verification = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains/{unconfigured['id']}/verify"
            )
            assert failed_verification.status_code == 409
            verified = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains/{domain['id']}/verify"
            )
            assert verified.status_code == 200
            assert verified.json()["verification_status"] == "VERIFIED"
            preview = client.get("/_local/tenant", headers={"Host": host})
            assert preview.status_code == 200
            assert preview.json()["tenant_id"] == first_tenant["id"]
            assert preview.json()["domain_status"] == "VERIFIED"
            requested = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/provisioning-jobs",
                json={"service_key": "catalogue_fixture"},
            )
            assert requested.status_code == 201
            assert requested.json()["status"] == "PENDING"
            duplicate_job = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/provisioning-jobs",
                json={"service_key": "catalogue_fixture"},
            )
            assert duplicate_job.status_code == 200
            assert duplicate_job.json()["id"] == requested.json()["id"]
            jobs = client.get(f"/api/v1/tenants/{first_tenant['id']}/provisioning-jobs").json()
            assert jobs == [duplicate_job.json()]
            retry = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/provisioning-jobs/"
                f"{requested.json()['id']}/retry"
            )
            assert retry.status_code == 409
            assert (
                client.get(f"/api/v1/tenants/{first_tenant['id']}/service-databases").json() == []
            )
            assert client.get("/_local/tenant", headers={"Host": host}).status_code == 404
            listed = client.get(f"/api/v1/tenants/{first_tenant['id']}/domains").json()
            assert {item["hostname"] for item in listed} == {host, unconfigured_host}
        session.close()
        transaction.rollback()
    engine.dispose()
