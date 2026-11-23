import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from media.auth import require_tenant_context
from media.config import Settings

SIGNING_SECRET = "test-only-signing-secret-at-least-32-bytes"


def context_token(tenant_id: str, database_name: str, secret_name: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": "platform-control-plane",
            "aud": "media-api",
            "iat": now,
            "exp": now + timedelta(minutes=1),
            "tenant_id": tenant_id,
            "hostname": f"admin.{tenant_id}.localhost",
            "database_name": database_name,
            "schema_name": "medfx",
            "runtime_role": f"{database_name}_medfx_rt",
            "secret_reference": f"local-volume://{secret_name}",
        },
        SIGNING_SECRET,
        algorithm="HS256",
    )


def app(tmp_path: Path) -> FastAPI:
    application = FastAPI()
    application.state.settings = Settings(
        database_url=None,
        schema="medfx",
        storage_root=tmp_path / "media",
        issuer="issuer",
        audience="media-api",
        jwks_url="jwks",
        max_upload_bytes=1024,
        max_pixels=100,
        tenant_context_signing_secret=SIGNING_SECRET,
        provisioned_secrets_dir=tmp_path,
        db_host="postgres",
        db_port=5432,
    )

    @application.get("/checked")
    def checked(request: Request, _context=Depends(require_tenant_context)) -> dict[str, str]:
        return {
            "database_name": request.state.tenant_settings.database_url.rsplit("/", 1)[1],
            "storage_root": request.state.tenant_settings.storage_root.name,
        }

    return application


def test_media_database_and_storage_are_tenant_scoped(tmp_path: Path):
    (tmp_path / "a.json").write_text(json.dumps({"runtime_password": "a"}))
    (tmp_path / "b.json").write_text(json.dumps({"runtime_password": "b"}))
    tenant_a, tenant_b = str(uuid4()), str(uuid4())
    with TestClient(app(tmp_path)) as client:
        response_a = client.get(
            "/checked",
            headers={"X-Tenant-Context": context_token(tenant_a, "tenant_a", "a.json")},
        )
        response_b = client.get(
            "/checked",
            headers={"X-Tenant-Context": context_token(tenant_b, "tenant_b", "b.json")},
        )
    assert response_a.json() == {"database_name": "tenant_a", "storage_root": tenant_a}
    assert response_b.json() == {"database_name": "tenant_b", "storage_root": tenant_b}


def test_missing_signed_context_is_rejected(tmp_path: Path):
    with TestClient(app(tmp_path)) as client:
        response = client.get("/checked", headers={"X-Tenant-Id": str(uuid4())})
    assert response.status_code == 404
