from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from identity_access.config.settings import Settings
from identity_access.dependencies.tenant import require_tenant_host
from identity_access.main import create_app


def test_unknown_host_fails_closed():
    app = FastAPI()
    app.state.settings = Settings(
        tenant_id=uuid4(),
        allowed_hosts=frozenset({"admin.lifemac.localhost"}),
        database_name="tenant",
        runtime_role="runtime",
        migrator_role="migrator",
        secret_file=Path("unused"),
    )

    @app.get("/checked")
    def checked(_: None = Depends(require_tenant_host)):
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/checked", headers={"Host": "unknown.localhost"}).status_code == 404
        assert (
            client.get("/checked", headers={"Host": "admin.lifemac.localhost"}).status_code == 200
        )
        assert (
            client.get("/checked", headers={"Host": "ADMIN.LIFEMAC.LOCALHOST."}).status_code == 200
        )


def test_protected_api_is_documented_as_bearer_authenticated():
    settings = Settings(
        tenant_id=uuid4(),
        allowed_hosts=frozenset({"admin.lifemac.localhost"}),
        database_name="tenant",
        runtime_role="runtime",
        migrator_role="migrator",
        secret_file=Path("unused"),
        oidc_issuer="http://localhost:8080/realms/platform-local",
        oidc_jwks_url="http://keycloak:8080/realms/platform-local/protocol/openid-connect/certs",
    )
    app = create_app(settings)
    schema = app.openapi()
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert schema["paths"]["/api/v1/me"]["get"]["security"] == [{"HTTPBearer": []}]
