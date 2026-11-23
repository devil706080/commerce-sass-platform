import json
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
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
                json={
                    "display_name": "  Example tenant  ",
                    "initial_owner_email": "  Owner@Example.COM ",
                },
                headers={"Idempotency-Key": key},
            )
            assert first.status_code == 201
            tenant = first.json()
            assert tenant["display_name"] == "Example tenant"
            assert tenant["initial_owner_email"] == "owner@example.com"
            assert tenant["status"] == "PENDING"
            themes = client.get("/api/v1/themes")
            assert themes.status_code == 200
            assert [theme["key"] for theme in themes.json()] == [
                "ocean_teal",
                "emerald",
                "indigo",
                "berry",
                "amber",
            ]
            branding = client.get(f"/api/v1/tenants/{tenant['id']}/branding")
            assert branding.status_code == 200
            assert branding.json()["display_name"] == "Example tenant"
            assert branding.json()["fallback_initials"] == "ET"
            assert branding.json()["theme_key"] == "ocean_teal"
            updated_branding = client.put(
                f"/api/v1/tenants/{tenant['id']}/branding",
                json={
                    "display_name": "Example Store",
                    "fallback_initials": "ES",
                    "theme_key": "berry",
                },
            )
            assert updated_branding.status_code == 200
            assert updated_branding.json()["theme_key"] == "berry"
            assert updated_branding.json()["palette"]["primary"] == "#A33B71"
            repeat = client.post(
                "/api/v1/tenants",
                json={
                    "display_name": "Example tenant",
                    "initial_owner_email": "owner@example.com",
                },
                headers={"Idempotency-Key": key},
            )
            assert repeat.status_code == 200
            assert repeat.json()["id"] == tenant["id"]
            conflict = client.post(
                "/api/v1/tenants",
                json={
                    "display_name": "Different",
                    "initial_owner_email": "owner@example.com",
                },
                headers={"Idempotency-Key": key},
            )
            assert conflict.status_code == 409
            duplicate = client.post(
                "/api/v1/tenants",
                json={
                    "display_name": " example TENANT ",
                    "initial_owner_email": "owner@example.com",
                },
                headers={"Idempotency-Key": str(uuid4())},
            )
            assert duplicate.status_code == 409
            assert duplicate.json() == {"detail": "A tenant with this name already exists"}
            assert client.get(f"/api/v1/tenants/{tenant['id']}").json() == tenant
            updated_contact = client.put(
                f"/api/v1/tenants/{tenant['id']}/owner-contact",
                json={"initial_owner_email": "NewOwner@Example.COM"},
            )
            assert updated_contact.status_code == 200
            assert updated_contact.json()["initial_owner_email"] == "newowner@example.com"
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
                json={
                    "display_name": f"Domain Test {uuid4().hex}",
                    "initial_owner_email": "owner@example.com",
                },
                headers={"Idempotency-Key": str(uuid4())},
            ).json()
            second_tenant = client.post(
                "/api/v1/tenants",
                json={
                    "display_name": f"Domain Conflict {uuid4().hex}",
                    "initial_owner_email": "owner@example.com",
                },
                headers={"Idempotency-Key": str(uuid4())},
            ).json()
            registered = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains",
                json={"hostname": host.upper() + "."},
            )
            assert registered.status_code == 201
            domain = registered.json()
            assert domain["hostname"] == host
            assert domain["purpose"] == "STOREFRONT"
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
            admin_domain = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains",
                json={"hostname": unconfigured_host, "purpose": "TENANT_ADMIN"},
            ).json()
            admin_verified = client.post(
                f"/api/v1/tenants/{first_tenant['id']}/domains/{admin_domain['id']}/verify"
            )
            assert admin_verified.status_code == 200
            assert admin_verified.json()["purpose"] == "TENANT_ADMIN"
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
            provisioning_preview = client.get("/_local/tenant", headers={"Host": host})
            assert provisioning_preview.status_code == 200
            assert provisioning_preview.json()["tenant_status"] == "PROVISIONING"
            listed = client.get(f"/api/v1/tenants/{first_tenant['id']}/domains").json()
            assert {item["hostname"] for item in listed} == {host, unconfigured_host}
            assert {item["purpose"] for item in listed} == {"STOREFRONT", "TENANT_ADMIN"}
        session.close()
        transaction.rollback()
    engine.dispose()


def test_active_tenant_can_enable_identity_access_without_lifecycle_regression(monkeypatch):
    host = f"identity-{uuid4().hex}.localhost"
    monkeypatch.setenv("APP_ENVIRONMENT", "local")
    monkeypatch.setenv("LOCAL_TENANT_LABELS", json.dumps({host: "Identity Test"}))
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
            tenant = client.post(
                "/api/v1/tenants",
                json={
                    "display_name": f"Identity Test {uuid4().hex}",
                    "initial_owner_email": "owner@example.com",
                },
                headers={"Idempotency-Key": str(uuid4())},
            ).json()
            domain = client.post(
                f"/api/v1/tenants/{tenant['id']}/domains",
                json={"hostname": host},
            ).json()
            assert (
                client.post(
                    f"/api/v1/tenants/{tenant['id']}/domains/{domain['id']}/verify"
                ).status_code
                == 200
            )
            session.execute(
                text("UPDATE tenants SET status = 'ACTIVE' WHERE id = :tenant"),
                {"tenant": tenant["id"]},
            )
            active_admin_domain = client.post(
                f"/api/v1/tenants/{tenant['id']}/domains",
                json={
                    "hostname": f"admin-{uuid4().hex}.localhost",
                    "purpose": "TENANT_ADMIN",
                },
            )
            assert active_admin_domain.status_code == 201
            assert (
                client.post(
                    f"/api/v1/tenants/{tenant['id']}/domains/"
                    f"{active_admin_domain.json()['id']}/verify"
                ).status_code
                == 200
            )
            requested = client.post(
                f"/api/v1/tenants/{tenant['id']}/provisioning-jobs",
                json={"service_key": "identity_access"},
            )
            assert requested.status_code == 201
            assert requested.json()["service_key"] == "identity_access"
            assert client.get(f"/api/v1/tenants/{tenant['id']}").json()["status"] == "ACTIVE"
        session.close()
        transaction.rollback()
    engine.dispose()
