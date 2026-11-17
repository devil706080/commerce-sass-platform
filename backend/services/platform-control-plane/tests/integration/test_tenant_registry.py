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
        session.close()
        transaction.rollback()
    engine.dispose()
