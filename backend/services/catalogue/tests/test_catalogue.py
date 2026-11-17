from uuid import UUID

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CATALOGUE_DATABASE_URL", "postgresql://unused")
    monkeypatch.setenv("TENANT_HOSTS", '{"lifemac.localhost":"49e84243-f9e4-4981-b3a5-38f943cc79ba"}')
    from catalogue import main

    return TestClient(main.app)


def test_invalid_tenant_context_is_rejected(client):
    response = client.get("/api/v1/products", headers={"X-Tenant-ID": str(UUID(int=1))})
    assert response.status_code in (403, 503)
