"""Allow multiple service schemas to reference one tenant database."""

from alembic import op

revision = "008_shared_db"
down_revision = "007_tenant_database_schemas"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "tenant_service_databases_database_name_key", "tenant_service_databases", type_="unique"
    )


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed recovery procedure")
