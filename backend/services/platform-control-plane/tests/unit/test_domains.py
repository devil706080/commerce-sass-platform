import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from platform_control_plane.main import create_app
from platform_control_plane.schemas.domain import DomainCreate


def test_domain_normalization_and_validation():
    domain = DomainCreate(hostname=" Store.Localhost. ")
    assert domain.hostname == "store.localhost"
    assert domain.purpose == "STOREFRONT"
    assert DomainCreate(hostname="admin.store.localhost", purpose="TENANT_ADMIN").purpose == (
        "TENANT_ADMIN"
    )
    with pytest.raises(ValidationError):
        DomainCreate(hostname="http://store.localhost:8000/path")
    with pytest.raises(ValidationError):
        DomainCreate(hostname="store.localhost", purpose="UNKNOWN")


def test_domain_routes_fail_closed(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test-secret")
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/tenants/00000000-0000-0000-0000-000000000001/domains",
            json={"hostname": "store.localhost"},
        )
    assert response.status_code == 403
