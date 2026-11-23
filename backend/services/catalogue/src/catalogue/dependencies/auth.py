from dataclasses import dataclass
import jwt
from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="Keycloak access token for a tenant-admin or platform-operator account.",
)

@dataclass(frozen=True)
class CatalogueIdentity:
    subject: str
    roles: tuple[str, ...]

def require_catalogue_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> CatalogueIdentity:
    settings = request.app.state.settings
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=503, detail="Catalogue authentication is unavailable")
    if credentials.scheme.lower() != "bearer" or not credentials.credentials or len(credentials.credentials) > 8192:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        token = credentials.credentials
        key = PyJWKClient(settings.oidc_jwks_url, timeout=3).get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["RS256"], audience=settings.oidc_audience, issuer=settings.oidc_issuer, options={"require": ["exp", "iat", "sub"]})
    except (jwt.PyJWTError, OSError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid access token") from None
    access = claims.get("realm_access")
    roles = access.get("roles", []) if isinstance(access, dict) else []
    subject = claims.get("sub")
    if not isinstance(subject, str) or not isinstance(roles, list):
        raise HTTPException(status_code=403, detail="Tenant authorization unavailable")
    if not any(role in roles for role in ("tenant-admin", "platform-operator")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return CatalogueIdentity(subject, tuple(str(role) for role in roles))
