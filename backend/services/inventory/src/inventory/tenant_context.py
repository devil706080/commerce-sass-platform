import json
from pathlib import Path
from urllib.parse import quote_plus

import jwt
from fastapi import Depends, Header, HTTPException, Request

from inventory.auth import InventoryIdentity, require_inventory_staff
from inventory.config import Settings


def inventory_context(
    request: Request,
    tenant_context: str | None = Header(None, alias="X-Tenant-Context"),
    identity: InventoryIdentity = Depends(require_inventory_staff),
) -> InventoryIdentity:
    settings: Settings = request.app.state.settings
    if not tenant_context or not settings.tenant_context_signing_secret:
        raise HTTPException(status_code=404, detail="Tenant context not found")
    try:
        claims = jwt.decode(
            tenant_context,
            settings.tenant_context_signing_secret,
            algorithms=["HS256"],
            audience="inventory-api",
            issuer="platform-control-plane",
            options={"require": ["exp", "iat", "iss", "aud", "tenant_id", "hostname", "database_name", "schema_name", "runtime_role", "secret_reference"]},
        )
        reference = str(claims["secret_reference"])
        filename = reference.removeprefix("local-volume://")
        if not reference.startswith("local-volume://") or not filename or Path(filename).name != filename:
            raise ValueError("invalid secret reference")
        secret = json.loads((settings.provisioned_secrets_dir / filename).read_text(encoding="utf-8"))
        database_url = "postgresql://{}:{}@{}:{}/{}".format(
            quote_plus(str(claims["runtime_role"])), quote_plus(secret["runtime_password"]),
            settings.db_host, settings.db_port, claims["database_name"],
        )
        request.state.tenant_settings = settings.with_database(database_url, str(claims["schema_name"]))
        request.state.tenant_id = str(claims["tenant_id"])
    except (jwt.PyJWTError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid tenant context") from None
    return identity
