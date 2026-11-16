import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from platform_control_plane.api.routes import health, readiness
from platform_control_plane.core.config import RuntimeSettings
from platform_control_plane.core.logging import log_event
from platform_control_plane.database.engine import create_runtime_engine


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = RuntimeSettings()  # type: ignore[call-arg]
    engine = create_runtime_engine(settings)
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield
    finally:
        engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Platform Control Plane", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(readiness.router)

    @app.middleware("http")
    async def correlation(request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = str(uuid4())
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001 - prevent unexpected errors leaking to clients
            log_event("request_failed", correlation_id)
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response.headers["X-Correlation-ID"] = correlation_id
        log_event("request_completed", correlation_id)
        return response

    return app


logging.getLogger("platform_control_plane").setLevel(logging.INFO)
app = create_app()
