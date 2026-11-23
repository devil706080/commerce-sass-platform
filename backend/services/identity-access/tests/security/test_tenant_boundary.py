from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from identity_access.config.settings import Settings
from identity_access.dependencies.tenant import require_tenant_host
from identity_access.main import create_app

SIGNING_SECRET = "test-only-tenant-context-secret-32-bytes-minimum"


def tenant_context(
    tenant_id: str,
    *,
    audience: str = "identity-api",
    database_name: str = "tenant_a",
    secret_reference: str = "local-volume://tenant-a.json",
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": "platform-control-plane",
            "aud": audience,
            "iat": now,
            "exp": now + timedelta(minutes=1),
            "tenant_id": tenant_id,
            "hostname": "admin.tenant-a.localhost",
            "database_name": database_name,
            "schema_name": "identity",
            "runtime_role": "tenant_a_identity_rt",
            "secret_reference": secret_reference,
        },
        SIGNING_SECRET,
        algorithm="HS256",
    )


def boundary_app(tmp_path: Path) -> FastAPI:
    app = FastAPI()
    app.state.settings = Settings(
        tenant_context_signing_secret=SIGNING_SECRET,
        provisioned_secrets_dir=tmp_path,
    )

    @app.get("/checked")
    def checked(settings: Settings = Depends(require_tenant_host)) -> dict[str, str]:
        return {
            "tenant_id": str(settings.tenant_id),
            "database_name": str(settings.database_name),
        }

    return app


def test_missing_or_wrong_audience_context_fails_closed(tmp_path: Path):
    tenant_id = str(uuid4())
    with TestClient(boundary_app(tmp_path)) as client:
        assert client.get("/checked").status_code == 404
        response = client.get(
            "/checked",
            headers={"X-Tenant-Context": tenant_context(tenant_id, audience="catalogue-api")},
        )
        assert response.status_code == 401


def test_signed_context_selects_only_its_tenant_database(tmp_path: Path):
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    with TestClient(boundary_app(tmp_path)) as client:
        response_a = client.get(
            "/checked", headers={"X-Tenant-Context": tenant_context(tenant_a)}
        )
        response_b = client.get(
            "/checked",
            headers={
                "X-Tenant-Context": tenant_context(
                    tenant_b,
                    database_name="tenant_b",
                    secret_reference="local-volume://tenant-b.json",
                )
            },
        )
    assert response_a.json() == {"tenant_id": tenant_a, "database_name": "tenant_a"}
    assert response_b.json() == {"tenant_id": tenant_b, "database_name": "tenant_b"}


def test_protected_api_is_documented_as_bearer_authenticated():
    settings = Settings(
        oidc_issuer="http://localhost:8080/realms/platform-local",
        oidc_jwks_url="http://keycloak:8080/realms/platform-local/protocol/openid-connect/certs",
        tenant_context_signing_secret=SIGNING_SECRET,
    )
    app = create_app(settings)
    schema = app.openapi()
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert schema["paths"]["/api/v1/me"]["get"]["security"] == [{"HTTPBearer": []}]
