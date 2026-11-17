from fastapi.testclient import TestClient

from platform_control_plane.main import create_app


def test_untrusted_headers_cannot_authorize_tenant_operations(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test-only")
    with TestClient(create_app()) as client:
        forged = {
            "Authorization": "Bearer forged-token",
            "X-Tenant-ID": "11111111-1111-1111-1111-111111111111",
            "X-Forwarded-Host": "tenant.example.com",
            "Idempotency-Key": "test-request",
        }
        requests = [
            client.get("/api/v1/tenants", headers=forged),
            client.get("/api/v1/tenants/11111111-1111-1111-1111-111111111111", headers=forged),
            client.post("/api/v1/tenants", headers=forged, json={"display_name": "Example"}),
        ]
        assert all(response.status_code == 403 for response in requests)
        assert all(
            response.json() == {"detail": "Operator access unavailable"} for response in requests
        )
