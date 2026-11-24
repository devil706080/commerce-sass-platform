from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from catalogue.schemas.extended import ImageCreate


@pytest.fixture
def client():
    from catalogue import main

    return TestClient(main.app)


def test_invalid_tenant_context_is_rejected(client):
    response = client.get("/api/v1/products", headers={"X-Tenant-ID": str(UUID(int=1))})
    assert response.status_code == 401


def test_product_image_accepts_stable_media_service_reference():
    reference = "/api/v1/media/3185280b-6a04-4382-abed-063878fb517a/content"
    assert ImageCreate(url=reference).url == reference


@pytest.mark.parametrize(
    "reference",
    [
        "/api/v1/media/not-a-uuid/content",
        "/api/v1/media/3185280b-6a04-4382-abed-063878fb517a/delete",
        "/api/tenant/media/api/v1/media/3185280b-6a04-4382-abed-063878fb517a/content",
    ],
)
def test_product_image_rejects_untrusted_relative_reference(reference):
    with pytest.raises(ValidationError):
        ImageCreate(url=reference)
