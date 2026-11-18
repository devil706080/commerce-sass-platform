from fastapi.testclient import TestClient

from catalogue.main import app
from catalogue.infrastructure.product_repository import ProductRepository
from catalogue.infrastructure.extended_repository import ExtendedRepository


def test_admin_routes_require_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/products")
    assert response.status_code in (401, 503)


def test_openapi_declares_bearer_authentication():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"


def test_public_catalogue_route_is_read_only(monkeypatch):
    monkeypatch.setattr(ProductRepository, "list", lambda *args, **kwargs: [])
    with TestClient(app) as client:
        response = client.get("/api/v1/store/products")
    assert response.status_code == 200
    assert response.json() == []


def test_public_categories_only_uses_catalogue_public_projection(monkeypatch):
    monkeypatch.setattr(ProductRepository, "public_categories", lambda *_: [])
    with TestClient(app) as client:
        response = client.get("/api/v1/store/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_public_product_category_filter_is_forwarded(monkeypatch):
    received = {}

    def list_products(_self, search, published, limit, offset, category_slug=None):
        received.update(search=search, published=published, limit=limit, offset=offset, category_slug=category_slug)
        return []

    monkeypatch.setattr(ProductRepository, "list", list_products)
    with TestClient(app) as client:
        response = client.get("/api/v1/store/products?category=wellness")
    assert response.status_code == 200
    assert received == {"search": None, "published": True, "limit": 50, "offset": 0, "category_slug": "wellness"}


def test_public_product_images_use_published_projection(monkeypatch):
    received = {}

    def public_images(_self, product_id):
        received["product_id"] = str(product_id)
        return []

    monkeypatch.setattr(ExtendedRepository, "public_images", public_images)
    product_id = "11111111-1111-1111-1111-111111111111"
    with TestClient(app) as client:
        response = client.get(f"/api/v1/store/products/{product_id}/images")
    assert response.status_code == 200
    assert received == {"product_id": product_id}
