from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Request, status
from jwt import PyJWKClient


@dataclass(frozen=True)
class Operator:
    issuer: str
    subject: str


def require_operator(request: Request) -> Operator:
    """Validate a signed operator access token; deny when configuration is absent."""
    settings = request.app.state.settings
    auth = request.headers.get("Authorization", "")
    if not all((settings.oidc_issuer, settings.oidc_audience, settings.oidc_jwks_url)):
        raise HTTPException(status_code=403, detail="Operator access unavailable")
    if not auth.startswith("Bearer ") or len(auth) > 8192:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        token = auth[7:]
        key = PyJWKClient(settings.oidc_jwks_url, timeout=3).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError, OSError, ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token") from None
    access = claims.get("realm_access")
    roles = access.get("roles", []) if isinstance(access, dict) else []
    if not isinstance(roles, list) or "platform-operator" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    issuer, subject = claims.get("iss"), claims.get("sub")
    if not isinstance(issuer, str) or not issuer or len(issuer) > 512:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if not isinstance(subject, str) or not subject or len(subject) > 255:
        raise HTTPException(status_code=401, detail="Invalid access token")
    return Operator(issuer=issuer, subject=subject)
