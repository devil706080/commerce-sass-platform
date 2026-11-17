from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from platform_control_plane.main import create_app


def test_signed_tokens_and_operator_role(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PLATFORM_CONTROL_RUNTIME_PASSWORD", "test-only")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example/realm")
    monkeypatch.setenv("OIDC_AUDIENCE", "control-api")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example/keys")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        "platform_control_plane.dependencies.operator.PyJWKClient",
        lambda *args, **kwargs: SimpleNamespace(
            get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())
        ),
    )
    now = datetime.now(UTC)
    claims = {
        "iss": "https://issuer.example/realm",
        "aud": "control-api",
        "sub": "operator",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "realm_access": {"roles": ["platform-operator"]},
    }
    app = create_app()
    with TestClient(app) as client:
        # Valid operator passes auth; invalid tenant ID is then rejected by request validation.
        token = jwt.encode(claims, key, algorithm="RS256")
        assert (
            client.get(
                "/api/v1/tenants/not-a-uuid", headers={"Authorization": f"Bearer {token}"}
            ).status_code
            == 422
        )
        claims["realm_access"] = {"roles": []}
        token = jwt.encode(claims, key, algorithm="RS256")
        assert (
            client.get("/api/v1/tenants", headers={"Authorization": f"Bearer {token}"}).status_code
            == 403
        )
        claims["aud"] = "wrong"
        token = jwt.encode(claims, key, algorithm="RS256")
        assert (
            client.get("/api/v1/tenants", headers={"Authorization": f"Bearer {token}"}).status_code
            == 401
        )
