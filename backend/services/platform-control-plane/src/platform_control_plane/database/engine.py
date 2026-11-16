from sqlalchemy import Engine, create_engine

from platform_control_plane.core.config import RuntimeSettings


def create_runtime_engine(settings: RuntimeSettings) -> Engine:
    return create_engine(
        settings.database_url(),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.db_connect_timeout},
        hide_parameters=True,
    )
