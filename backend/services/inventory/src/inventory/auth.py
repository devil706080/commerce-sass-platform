from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

bearer = HTTPBearer(bearerFormat="JWT", description="Tenant staff Keycloak access token")


@dataclass(frozen=True)
class InventoryIdentity:
    subject: str
    roles: tuple[str, ...]


def require_inventory_staff(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> InventoryIdentity:
    settings = request.app.state.settings
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=503, detail="Inventory authentication is unavailable")
    if credentials.scheme.lower() != "bearer" or len(credentials.credentials) > 8192:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        signing_key = PyJWKClient(settings.oidc_jwks_url, timeout=3).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except (jwt.PyJWTError, OSError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid access token") from None
    access = claims.get("realm_access")
    roles = access.get("roles", []) if isinstance(access, dict) else []
    subject = claims.get("sub")
    if not isinstance(subject, str) or not isinstance(roles, list):
        raise HTTPException(status_code=403, detail="Tenant authorization unavailable")
    allowed = {"tenant-admin", "inventory-manager", "platform-operator"}
    if not allowed.intersection(map(str, roles)):
        raise HTTPException(status_code=403, detail="Inventory permission denied")
    return InventoryIdentity(subject=subject, roles=tuple(map(str, roles)))
