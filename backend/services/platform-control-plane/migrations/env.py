from alembic import context
from sqlalchemy import create_engine, pool

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
    engine.dispose()
