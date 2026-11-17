from dataclasses import dataclass
import jwt
from fastapi import HTTPException, Request, status
from jwt import PyJWKClient

@dataclass(frozen=True)
class CatalogueIdentity:
    subject: str
    tenant_id: str
    roles: tuple[str, ...]

def require_catalogue_admin(request: Request) -> CatalogueIdentity:
    settings = request.app.state.settings
    auth = request.headers.get("Authorization", "")
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=503, detail="Catalogue authentication is unavailable")
    if not auth.startswith("Bearer ") or len(auth) > 8192:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        token = auth[7:]
        key = PyJWKClient(settings.oidc_jwks_url, timeout=3).get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["RS256"], audience=settings.oidc_audience, issuer=settings.oidc_issuer, options={"require": ["exp", "iat", "sub"]})
    except (jwt.PyJWTError, OSError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid access token") from None
    access = claims.get("realm_access")
    roles = access.get("roles", []) if isinstance(access, dict) else []
    tenant_id = claims.get("tenant_id")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not isinstance(tenant_id, str) or not isinstance(roles, list):
        raise HTTPException(status_code=403, detail="Tenant authorization unavailable")
    if not any(role in roles for role in ("tenant-admin", "platform-operator")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return CatalogueIdentity(subject, tenant_id, tuple(str(role) for role in roles))
