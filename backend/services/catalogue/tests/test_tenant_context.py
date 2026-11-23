import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from catalogue.config.settings import Settings
from catalogue.dependencies.auth import CatalogueIdentity, require_catalogue_admin
from catalogue.dependencies.context import admin_context

SIGNING_SECRET = "test-only-signing-secret-at-least-32-bytes"


def context_token(tenant_id: str, database_name: str, secret_name: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": "platform-control-plane",
            "aud": "catalogue-api",
            "iat": now,
            "exp": now + timedelta(minutes=1),
            "tenant_id": tenant_id,
            "hostname": f"admin.{tenant_id}.localhost",
            "database_name": database_name,
            "schema_name": "catfx",
            "runtime_role": f"{database_name}_catfx_rt",
            "secret_reference": f"local-volume://{secret_name}",
        },
        SIGNING_SECRET,
        algorithm="HS256",
    )


def app(tmp_path: Path) -> FastAPI:
    application = FastAPI()
    application.state.settings = Settings(
        database_url=None,
        schema_name="catfx",
        tenant_context_signing_secret=SIGNING_SECRET,
        provisioned_secrets_dir=tmp_path,
    )
    application.dependency_overrides[require_catalogue_admin] = lambda: CatalogueIdentity(
        "subject", ("tenant-admin",)
    )

    @application.get("/checked")
    def checked(request: Request, _identity=Depends(admin_context)) -> dict[str, str]:
        return {
            "database_name": request.state.tenant_settings.database_url.rsplit("/", 1)[1],
            "schema": request.state.tenant_settings.schema_name,
        }

    return application


def test_context_routes_each_tenant_to_its_own_database(tmp_path: Path):
    (tmp_path / "a.json").write_text(json.dumps({"runtime_password": "a"}))
    (tmp_path / "b.json").write_text(json.dumps({"runtime_password": "b"}))
    with TestClient(app(tmp_path)) as client:
        response_a = client.get(
            "/checked",
            headers={"X-Tenant-Context": context_token(str(uuid4()), "tenant_a", "a.json")},
        )
        response_b = client.get(
            "/checked",
            headers={"X-Tenant-Context": context_token(str(uuid4()), "tenant_b", "b.json")},
        )
    assert response_a.json() == {"database_name": "tenant_a", "schema": "catfx"}
    assert response_b.json() == {"database_name": "tenant_b", "schema": "catfx"}


def test_unsigned_browser_tenant_selection_is_rejected(tmp_path: Path):
    with TestClient(app(tmp_path)) as client:
        response = client.get("/checked", headers={"X-Tenant-Id": str(uuid4())})
    assert response.status_code == 404
