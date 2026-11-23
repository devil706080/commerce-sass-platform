from fastapi import HTTPException, Request


def require_tenant_host(request: Request) -> None:
    hostname = (request.url.hostname or "").lower().rstrip(".")
    if hostname not in request.app.state.settings.allowed_hosts:
        raise HTTPException(status_code=404, detail="Tenant host not found")
