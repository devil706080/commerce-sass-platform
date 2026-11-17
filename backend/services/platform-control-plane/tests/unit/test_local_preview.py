import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from platform_control_plane.core.config import RuntimeSettings
from platform_control_plane.main import create_app


def test_local_preview_is_environment_configured(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test")
    monkeypatch.setenv("APP_ENVIRONMENT", "local")
    monkeypatch.setenv("LOCAL_TENANT_LABELS", '{"localhost":"Example Store"}')
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/_local/tenant").json()["display_name"] == "Example Store"
        assert (
            client.get("/_local/tenant", headers={"Host": "unknown.localhost"}).status_code == 404
        )
        assert client.get("/api/v1/tenants").status_code == 403


def test_local_preview_is_disabled_in_production(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test")
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.delenv("LOCAL_TENANT_LABELS", raising=False)
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/_local/tenant").status_code == 404


def test_rejects_public_host_and_production_mapping():
    with pytest.raises(ValidationError):
        RuntimeSettings(
            db_host="localhost",
            platform_control_runtime_password="x",
            app_environment="local",
            local_tenant_labels='{"example.com":"Store"}',
        )
    with pytest.raises(ValidationError):
        RuntimeSettings(
            db_host="localhost",
            platform_control_runtime_password="x",
            app_environment="production",
            local_tenant_labels='{"localhost":"Store"}',
        )
