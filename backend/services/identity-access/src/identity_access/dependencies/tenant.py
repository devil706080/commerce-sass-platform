from dataclasses import replace
from pathlib import Path
from uuid import UUID

import jwt
from fastapi import Header, HTTPException, Request

from identity_access.config.settings import Settings


def require_tenant_host(request: Request, tenant_context: str | None = Header(None, alias="X-Tenant-Context")) -> Settings:
    settings: Settings = request.app.state.settings
    if not tenant_context or not settings.tenant_context_signing_secret:
        raise HTTPException(status_code=404, detail="Tenant context not found")
    try:
        claims = jwt.decode(tenant_context, settings.tenant_context_signing_secret, algorithms=["HS256"], audience="identity-api", issuer="platform-control-plane", options={"require": ["exp", "iat", "iss", "aud", "tenant_id", "hostname"]})
        reference = str(claims["secret_reference"])
        filename = reference.removeprefix("local-volume://")
        if (
            not reference.startswith("local-volume://")
            or not filename
            or Path(filename).name != filename
        ):
            raise ValueError("invalid secret reference")
        tenant_settings = replace(
            settings,
            tenant_id=UUID(str(claims["tenant_id"])),
            allowed_hosts=frozenset({str(claims["hostname"])}),
            database_name=str(claims["database_name"]),
            runtime_role=str(claims["runtime_role"]),
            schema_name=str(claims["schema_name"]),
            secret_file=settings.provisioned_secrets_dir / filename,
            initial_owner_email=(
                str(claims["initial_owner_email"]).strip().casefold()
                if claims.get("initial_owner_email")
                else None
            ),
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid tenant context") from None
    request.state.tenant_settings = tenant_settings
    return tenant_settings
