"""Add durable provisioning jobs and service database references."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "006_provisioning_jobs"
down_revision = "005_tenant_domains"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_tenant_status", "tenants", type_="check")
    op.create_check_constraint(
        "ck_tenant_status",
        "tenants",
        "status IN ('PENDING', 'PROVISIONING', 'FAILED', 'DELETION_REQUESTED')",
    )
    op.create_table(
        "provisioning_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("service_key", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "service_key", name="uq_provisioning_tenant_service"),
        sa.CheckConstraint(
            "service_key IN ('catalogue_fixture', 'inventory_fixture')",
            name="ck_provisioning_service_key",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'INFRASTRUCTURE_READY', 'FAILED')",
            name="ck_provisioning_job_status",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_provisioning_attempt_count"),
    )
    op.create_index(
        "ix_provisioning_jobs_status_created", "provisioning_jobs", ["status", "created_at"]
    )
    op.create_table(
        "tenant_service_databases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("service_key", sa.String(32), nullable=False),
        sa.Column("database_name", sa.String(63), nullable=False, unique=True),
        sa.Column("runtime_role", sa.String(63), nullable=False, unique=True),
        sa.Column("migrator_role", sa.String(63), nullable=False, unique=True),
        sa.Column("secret_reference", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="INFRASTRUCTURE_READY"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "service_key", name="uq_service_database_tenant_service"),
        sa.CheckConstraint("status = 'INFRASTRUCTURE_READY'", name="ck_service_database_status"),
    )
    for table in ("provisioning_jobs", "tenant_service_databases"):
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM platform_control_runtime")
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM platform_control_worker")
    op.execute("GRANT SELECT, INSERT ON public.provisioning_jobs TO platform_control_runtime")
    op.execute(
        "GRANT UPDATE (status, error_code, updated_at) ON public.provisioning_jobs "
        "TO platform_control_runtime"
    )
    op.execute("GRANT SELECT, UPDATE ON public.provisioning_jobs TO platform_control_worker")
    op.execute("GRANT SELECT ON public.tenant_service_databases TO platform_control_runtime")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON public.tenant_service_databases TO platform_control_worker"
    )


def downgrade():
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
