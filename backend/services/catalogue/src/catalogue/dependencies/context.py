import json
from dataclasses import replace
from pathlib import Path
from urllib.parse import quote_plus

import jwt
from fastapi import Depends, Header, HTTPException, Request

from catalogue.config.settings import Settings
from catalogue.dependencies.auth import CatalogueIdentity, require_catalogue_admin


def admin_context(
    request: Request,
    tenant_context: str | None = Header(None, alias="X-Tenant-Context"),
    identity: CatalogueIdentity = Depends(require_catalogue_admin),
) -> CatalogueIdentity:
    settings: Settings = request.app.state.settings
    if not tenant_context or not settings.tenant_context_signing_secret:
        raise HTTPException(status_code=404, detail="Tenant context not found")
    try:
        claims = jwt.decode(
            tenant_context,
            settings.tenant_context_signing_secret,
            algorithms=["HS256"],
            audience="catalogue-api",
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
        reference = str(claims["secret_reference"])
        filename = reference.removeprefix("local-volume://")
        if (
            not reference.startswith("local-volume://")
            or not filename
            or Path(filename).name != filename
        ):
            raise ValueError("invalid secret reference")
        payload = json.loads((settings.provisioned_secrets_dir / filename).read_text(encoding="utf-8"))
        database_url = "postgresql://{}:{}@{}:{}/{}".format(
            quote_plus(str(claims["runtime_role"])),
            quote_plus(payload["runtime_password"]),
            settings.db_host,
            settings.db_port,
            claims["database_name"],
        )
        request.state.tenant_settings = replace(
            settings,
            database_url=database_url,
            schema_name=str(claims["schema_name"]),
        )
    except (jwt.PyJWTError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid tenant context") from None
    return identity
