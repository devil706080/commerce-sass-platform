from fastapi.testclient import TestClient

from inventory.main import app


def test_health_is_public() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "inventory"}


def test_inventory_requires_authentication() -> None:
    response = TestClient(app).get("/api/v1/stock-items")
    assert response.status_code in {401, 403}


def test_batch_endpoints_require_authentication() -> None:
    response = TestClient(app).get(
        "/api/v1/stock-items/00000000-0000-0000-0000-000000000001/batches"
    )
    assert response.status_code in {401, 403}


def test_dashboard_summary_requires_authentication() -> None:
    response = TestClient(app).get("/api/v1/dashboard/summary")
    assert response.status_code in {401, 403}


def test_inventory_alerts_require_authentication() -> None:
    response = TestClient(app).get("/api/v1/alerts?type=LOW_STOCK")
    assert response.status_code in {401, 403}
