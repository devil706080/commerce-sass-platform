from uuid import UUID

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from catalogue import main

    return TestClient(main.app)


def test_invalid_tenant_context_is_rejected(client):
    response = client.get("/api/v1/products", headers={"X-Tenant-ID": str(UUID(int=1))})
    assert response.status_code == 401
