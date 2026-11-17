from alembic import context
from sqlalchemy import create_engine, pool, text

from platform_control_plane.core.config import MigrationSettings

settings = MigrationSettings()
url = settings.database_url()
target_metadata = None

if context.is_offline_mode():
    context.configure(url=url.render_as_string(hide_password=False), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool, connect_args={"connect_timeout": 5})
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
            # The local database grants runtime access to new tables by default.
            # Migration history is an exception and remains migrator-only.
            if connection.execute(text("SELECT to_regclass('public.alembic_version')")).scalar():
                connection.execute(
                    text("REVOKE ALL ON TABLE public.alembic_version FROM platform_control_runtime")
                )
    engine.dispose()
