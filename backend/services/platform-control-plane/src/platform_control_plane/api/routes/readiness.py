from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from platform_control_plane.dependencies.database import get_session
from platform_control_plane.schemas.health import StatusResponse

router = APIRouter()


@router.get("/ready", response_model=StatusResponse, responses={503: {"model": StatusResponse}})
def readiness(session: Annotated[Session, Depends(get_session)]) -> StatusResponse | JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return StatusResponse(status="ok")
