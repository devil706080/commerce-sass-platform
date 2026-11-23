from typing import Annotated

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from identity_access.domain.models import AuthenticatedIdentity

bearer = HTTPBearer(bearerFormat="JWT", auto_error=False)


def require_identity(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> AuthenticatedIdentity:
    settings = request.app.state.settings
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    if not credentials.credentials or len(credentials.credentials) > 8192:
        raise HTTPException(status_code=401, detail="Invalid access token")
    try:
        key = request.app.state.jwks_client.get_signing_key_from_jwt(
            credentials.credentials
        )
        claims = jwt.decode(
            credentials.credentials,
            key.key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            options={"require": ["exp", "iat", "iss", "sub", "email"]},
        )
    except jwt.PyJWTError, OSError, ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token") from None
    roles_claim = claims.get("realm_access")
    roles = roles_claim.get("roles", []) if isinstance(roles_claim, dict) else []
    subject, issuer, email = claims.get("sub"), claims.get("iss"), claims.get("email")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if not isinstance(issuer, str) or not issuer:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if not isinstance(email, str) or not email:
        raise HTTPException(status_code=401, detail="Invalid access token")
    if claims.get("email_verified") is not True:
        raise HTTPException(status_code=403, detail="Verified email is required")
    return AuthenticatedIdentity(
        issuer=issuer,
        subject=subject,
        email=email.strip().casefold(),
        display_name=claims.get("name") if isinstance(claims.get("name"), str) else None,
        realm_roles=tuple(str(role) for role in roles if isinstance(role, str)),
    )
