"""Track owning-service migration and smoke-check readiness."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "009_service_ready"
down_revision = "008_shared_db"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenant_service_readiness",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("service_key", sa.String(32), nullable=False),
        sa.Column("migration_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("smoke_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "service_key", name="uq_service_readiness_tenant_service"),
        sa.CheckConstraint(
            "migration_status IN ('PENDING','MIGRATED','FAILED')", name="ck_readiness_migration"
        ),
        sa.CheckConstraint(
            "smoke_status IN ('PENDING','PASSED','FAILED')", name="ck_readiness_smoke"
        ),
    )
    op.execute("REVOKE ALL ON TABLE public.tenant_service_readiness FROM platform_control_runtime")
    op.execute("GRANT SELECT ON public.tenant_service_readiness TO platform_control_runtime")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON public.tenant_service_readiness TO platform_control_worker"
    )


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed recovery migration")
