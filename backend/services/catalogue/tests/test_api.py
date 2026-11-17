from fastapi.testclient import TestClient

from catalogue.main import app
from catalogue.infrastructure.product_repository import ProductRepository


def test_admin_routes_require_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/products")
    assert response.status_code in (401, 503)


def test_public_catalogue_route_is_read_only(monkeypatch):
    monkeypatch.setattr(ProductRepository, "list", lambda *args, **kwargs: [])
    with TestClient(app) as client:
        response = client.get("/api/v1/store/products")
    assert response.status_code == 200
    assert response.json() == []
