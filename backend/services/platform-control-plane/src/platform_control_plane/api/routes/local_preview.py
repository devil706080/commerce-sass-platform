from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


class LocalPreview(BaseModel):
    display_name: str
    notice: str = "Local preview only; not tenant authorization or domain verification."


router = APIRouter()


@router.get("/_local/tenant", response_model=LocalPreview, include_in_schema=False)
def local_preview(request: Request) -> LocalPreview:
    settings = request.app.state.settings
    if settings.app_environment != "local":
        raise HTTPException(status_code=404, detail="Not found")
    hostname = request.url.hostname
    name = settings.local_labels().get(hostname or "")
    if name is None:
        raise HTTPException(status_code=404, detail="Local tenant preview not configured")
    return LocalPreview(display_name=name)
