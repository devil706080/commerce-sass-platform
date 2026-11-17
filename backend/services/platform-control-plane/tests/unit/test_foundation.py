import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from platform_control_plane.core.config import MigrationSettings, RuntimeSettings
from platform_control_plane.dependencies.database import get_session
from platform_control_plane.main import create_app


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test-secret")


def test_settings_require_password(monkeypatch):
    monkeypatch.delenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", raising=False)
    with pytest.raises(ValidationError):
        RuntimeSettings(db_host="localhost")


def test_settings_bound_pool_and_distinct_identities():
    runtime = RuntimeSettings(db_host="localhost", platform_control_runtime_password="secret")
    migration = MigrationSettings(db_host="localhost", platform_control_migrator_password="secret")
    assert runtime.database_url().username == "platform_control_runtime"
    assert migration.database_url().username == "platform_control_migrator"
    assert "secret" not in repr(runtime)
    with pytest.raises(ValidationError):
        RuntimeSettings(db_host="localhost", platform_control_runtime_password="x", db_pool_size=99)


def test_health_requires_no_database(configured):
    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_console_cors_allows_authenticated_delete(configured, monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    with TestClient(create_app()) as client:
        response = client.options(
            "/api/v1/tenants/00000000-0000-0000-0000-000000000001",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "authorization",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "DELETE" in response.headers["access-control-allow-methods"]


def test_startup_requires_configuration(monkeypatch):
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", raising=False)
    with pytest.raises(ValidationError), TestClient(create_app()):
        pass


def test_unexpected_error_is_sanitized(configured, caplog):
    app = create_app()

    @app.get("/failure")
    def failure():
        raise RuntimeError("private-test-secret")

    with caplog.at_level(logging.INFO), TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")
    assert response.status_code == 500
    assert "private-test-secret" not in response.text + caplog.text


def test_readiness_hides_database_errors(configured, caplog):
    class BrokenSession:
        def execute(self, statement):
            raise OperationalError("secret SQL", {}, Exception("secret-password"))

    app = create_app()
    app.dependency_overrides[get_session] = lambda: BrokenSession()
    with caplog.at_level(logging.INFO), TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "secret-password" not in response.text + caplog.text
    assert response.headers["X-Correlation-ID"]
