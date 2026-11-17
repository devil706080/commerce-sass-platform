from uuid import UUID
from fastapi import Header, HTTPException
from catalogue.config.settings import Settings

def resolve_tenant(settings: Settings, host: str | None = Header(default=None, alias="Host"), requested: str | None = Header(default=None, alias="X-Tenant-ID")) -> UUID:
    # `requested` is passed by protected routes from the verified JWT claim;
    # browser-provided X-Tenant-ID headers are never used for authorization.
    resolved = requested or settings.tenant_hosts.get((host or "").split(":", 1)[0])
    if not resolved:
        raise HTTPException(status_code=400, detail="Tenant context is required")
    try:
        return UUID(resolved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid tenant context") from exc
