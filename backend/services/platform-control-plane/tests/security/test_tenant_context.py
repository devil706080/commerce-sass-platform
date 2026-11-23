from types import SimpleNamespace
from uuid import uuid4

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from platform_control_plane.api.routes.tenant_context import router
from platform_control_plane.dependencies.database import get_session

BROKER_TOKEN = "test-only-broker-token"
SIGNING_SECRET = "test-only-signing-secret-at-least-32-bytes"


class Result:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row

    def scalars(self):
        return self

    def all(self):
        return self.row


class TenantSession:
    def execute(self, _statement, parameters=None):
        if parameters is None:
            return Result(["admin.tenant-a.localhost", "admin.tenant-b.localhost"])
        if parameters != {"hostname": "admin.tenant-a.localhost", "service": "catalogue_fixture"}:
            return Result(None)
        return Result(
            {
                "tenant_id": uuid4(),
                "hostname": "admin.tenant-a.localhost",
                "database_name": "tenant_a",
                "schema_name": "catfx",
                "runtime_role": "tenant_a_catfx_rt",
                "secret_reference": "local-volume://tenant-a.json",
            }
        )


def app() -> FastAPI:
    application = FastAPI()
    application.state.settings = SimpleNamespace(
        tenant_context_broker_token=SecretStr(BROKER_TOKEN),
        tenant_context_signing_secret=SecretStr(SIGNING_SECRET),
    )
    application.include_router(router)
    application.dependency_overrides[get_session] = lambda: TenantSession()
    return application


def test_unknown_hostname_cannot_receive_another_tenant_context():
    with TestClient(app()) as client:
        response = client.post(
            "/_internal/tenant-context?service_key=catalogue_fixture",
            headers={
                "Authorization": f"Bearer {BROKER_TOKEN}",
                "X-Forwarded-Host": "admin.tenant-b.localhost:3001",
            },
        )
    assert response.status_code == 404


def test_context_is_service_scoped_and_contains_no_password():
    with TestClient(app()) as client:
        response = client.post(
            "/_internal/tenant-context?service_key=catalogue_fixture",
            headers={
                "Authorization": f"Bearer {BROKER_TOKEN}",
                "X-Forwarded-Host": "admin.tenant-a.localhost:3001",
            },
        )
    assert response.status_code == 200
    claims = jwt.decode(
        response.json()["token"],
        SIGNING_SECRET,
        algorithms=["HS256"],
        audience="catalogue-api",
        issuer="platform-control-plane",
    )
    assert claims["database_name"] == "tenant_a"
    assert "password" not in claims


def test_verified_admin_domains_are_available_only_to_internal_sync():
    with TestClient(app()) as client:
        denied = client.get("/_internal/tenant-admin-domains")
        allowed = client.get(
            "/_internal/tenant-admin-domains",
            headers={"Authorization": f"Bearer {BROKER_TOKEN}"},
        )
    assert denied.status_code == 401
    assert allowed.json() == {
        "hostnames": ["admin.tenant-a.localhost", "admin.tenant-b.localhost"]
    }
