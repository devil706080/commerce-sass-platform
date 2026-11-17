"""Create the initial tenant registry and creation audit records.

Revision ID: 001_tenant_registry
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "001_tenant_registry"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("status = 'PENDING'", name="ck_tenant_pending"),
        sa.CheckConstraint("length(trim(display_name)) > 0", name="ck_tenant_display_name"),
    )
    op.create_table(
        "tenant_create_idempotency",
        sa.Column("request_key", sa.String(128), primary_key=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "tenant_audit_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    for table in ("tenants", "tenant_create_idempotency", "tenant_audit_events"):
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM platform_control_runtime")
    op.execute("GRANT SELECT, INSERT ON public.tenants TO platform_control_runtime")
    op.execute(
        "GRANT SELECT, INSERT ON public.tenant_create_idempotency TO platform_control_runtime"
    )
    op.execute("GRANT INSERT ON public.tenant_audit_events TO platform_control_runtime")


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed recovery procedure")
