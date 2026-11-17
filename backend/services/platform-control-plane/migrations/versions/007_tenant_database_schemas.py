"""Add one database per tenant with service-scoped schemas."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "007_tenant_database_schemas"
down_revision = "006_provisioning_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenant_databases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("database_name", sa.String(63), nullable=False, unique=True),
        sa.Column("owner_role", sa.String(63), nullable=False, unique=True),
        sa.Column("secret_reference", sa.String(512), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_database_tenant"),
    )
    op.add_column(
        "tenant_service_databases",
        sa.Column("tenant_database_id", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "tenant_service_databases", sa.Column("schema_name", sa.String(63), nullable=True)
    )
    op.create_foreign_key(
        "fk_service_database_tenant_database",
        "tenant_service_databases",
        "tenant_databases",
        ["tenant_database_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_service_database_tenant_schema",
        "tenant_service_databases",
        ["tenant_database_id", "schema_name"],
    )
    op.execute("GRANT SELECT ON public.tenant_databases TO platform_control_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON public.tenant_databases TO platform_control_worker")


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed recovery procedure")
