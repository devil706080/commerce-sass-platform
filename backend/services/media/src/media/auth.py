import json
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import quote_plus

import jwt
from fastapi import Depends, Header, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

bearer_scheme = HTTPBearer(bearerFormat="JWT")


@dataclass(frozen=True)
class Identity:
    subject: str
    roles: tuple[str, ...]


def require_media_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Identity:
    settings = request.app.state.settings
    if not all((settings.issuer, settings.audience, settings.jwks_url)):
        raise HTTPException(503, "Media authentication is unavailable")
    try:
        claims = jwt.decode(credentials.credentials, PyJWKClient(settings.jwks_url, timeout=3).get_signing_key_from_jwt(credentials.credentials).key, algorithms=["RS256"], audience=settings.audience, issuer=settings.issuer, options={"require": ["exp", "iat", "sub"]})
    except (jwt.PyJWTError, OSError, ValueError):
        raise HTTPException(401, "Invalid access token") from None
    roles = claims.get("realm_access", {}).get("roles", [])
    subject = claims.get("sub")
    if not isinstance(subject, str) or not isinstance(roles, list) or not any(role in roles for role in ("tenant-admin", "platform-operator")):
        raise HTTPException(403, "Tenant authorization unavailable")
    return Identity(subject, tuple(str(role) for role in roles))


def require_tenant_context(
    request: Request,
    tenant_context: str | None = Header(None, alias="X-Tenant-Context"),
) -> None:
    settings = request.app.state.settings
    if not tenant_context or not settings.tenant_context_signing_secret:
        raise HTTPException(404, "Tenant context not found")
    try:
        context = jwt.decode(
            tenant_context,
            settings.tenant_context_signing_secret,
            algorithms=["HS256"],
            audience="media-api",
            issuer="platform-control-plane",
            options={
                "require": [
                    "exp",
                    "iat",
                    "iss",
                    "aud",
                    "tenant_id",
                    "hostname",
                    "database_name",
                    "schema_name",
                    "runtime_role",
                    "secret_reference",
                ]
            },
        )
        reference = str(context["secret_reference"])
        filename = reference.removeprefix("local-volume://")
        if (
            not reference.startswith("local-volume://")
            or not filename
            or Path(filename).name != filename
        ):
            raise ValueError("invalid secret reference")
        payload = json.loads(
            (settings.provisioned_secrets_dir / filename).read_text(encoding="utf-8")
        )
        database_url = "postgresql://{}:{}@{}:{}/{}".format(
            quote_plus(str(context["runtime_role"])),
            quote_plus(payload["runtime_password"]),
            settings.db_host,
            settings.db_port,
            context["database_name"],
        )
        request.state.tenant_settings = replace(
            settings,
            database_url=database_url,
            schema=str(context["schema_name"]),
            storage_root=settings.storage_root / str(context["tenant_id"]),
        )
    except (jwt.PyJWTError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(401, "Invalid tenant context") from None


def require_tenant_admin(
    identity: Identity = Depends(require_media_identity),
    _context: None = Depends(require_tenant_context),
) -> Identity:
    return identity
