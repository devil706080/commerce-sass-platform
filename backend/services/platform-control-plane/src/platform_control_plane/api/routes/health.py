from fastapi import APIRouter

from platform_control_plane.schemas.health import StatusResponse

router = APIRouter()


@router.get("/health", response_model=StatusResponse)
def health() -> StatusResponse:
    return StatusResponse(status="ok")
