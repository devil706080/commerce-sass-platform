from dataclasses import dataclass
import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

bearer_scheme = HTTPBearer(bearerFormat="JWT")


@dataclass(frozen=True)
class Identity:
    tenant_id: str


def require_tenant_admin(request: Request, credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> Identity:
    settings = request.app.state.settings
    if not all((settings.issuer, settings.audience, settings.jwks_url)):
        raise HTTPException(503, "Media authentication is unavailable")
    try:
        claims = jwt.decode(credentials.credentials, PyJWKClient(settings.jwks_url, timeout=3).get_signing_key_from_jwt(credentials.credentials).key, algorithms=["RS256"], audience=settings.audience, issuer=settings.issuer, options={"require": ["exp", "iat", "sub"]})
    except (jwt.PyJWTError, OSError, ValueError):
        raise HTTPException(401, "Invalid access token") from None
    roles = claims.get("realm_access", {}).get("roles", [])
    tenant_id = claims.get("tenant_id")
    if not isinstance(tenant_id, str) or not isinstance(roles, list) or not any(role in roles for role in ("tenant-admin", "platform-operator")):
        raise HTTPException(403, "Tenant authorization unavailable")
    return Identity(tenant_id)
