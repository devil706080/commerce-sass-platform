from fastapi.testclient import TestClient

from platform_control_plane.main import create_app


def test_tenant_routes_fail_closed(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test-secret")
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/tenants").status_code == 403
        assert (
            client.post(
                "/api/v1/tenants",
                json={"display_name": "Example"},
                headers={"Idempotency-Key": "example"},
            ).status_code
            == 403
        )
        assert (
            client.delete("/api/v1/tenants/00000000-0000-0000-0000-000000000001").status_code == 403
        )
