import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker

from platform_control_plane.core.config import RuntimeSettings
from platform_control_plane.database.engine import create_runtime_engine
from platform_control_plane.database.session import session_scope
from platform_control_plane.main import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("RUN_DB_INTEGRATION"), reason="requires local PostgreSQL credentials"
    ),
]


def test_runtime_connection_and_permissions():
    engine = create_runtime_engine(RuntimeSettings())
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT current_user, current_database(), "
                "has_schema_privilege(current_user, 'public', 'CREATE'), "
                "(SELECT rolsuper FROM pg_roles WHERE rolname=current_user)"
            )
        ).one()
        assert tuple(row) == ("platform_control_runtime", "platform_control", False, False)
        assert not conn.execute(
            text("SELECT has_table_privilege(current_user, 'public.alembic_version', 'UPDATE')")
        ).scalar_one()
        with pytest.raises(ProgrammingError):
            conn.execute(text("CREATE TABLE public.runtime_permission_test (id integer)"))
    engine.dispose()


def test_readiness_and_session_cleanup():
    engine = create_runtime_engine(RuntimeSettings())
    sessions = session_scope(sessionmaker(bind=engine))
    session = next(sessions)
    assert session.execute(text("SELECT 1")).scalar_one() == 1
    sessions.close()
    assert engine.pool.checkedout() == 0
    engine.dispose()
    with TestClient(create_app()) as client:
        assert client.get("/ready").status_code == 200
