"""Create local tenant-domain registration and verification records."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "005_tenant_domains"
down_revision = "004_tenant_deletion_request"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenant_domains",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column("hostname", sa.String(253), nullable=False, unique=True),
        sa.Column(
            "verification_status",
            sa.String(24),
            nullable=False,
            server_default="PENDING_VERIFICATION",
        ),
        sa.Column("verification_method", sa.String(16), nullable=False, server_default="LOCAL"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "verification_status IN ('PENDING_VERIFICATION', 'VERIFIED')",
            name="ck_tenant_domain_verification_status",
        ),
        sa.CheckConstraint("verification_method = 'LOCAL'", name="ck_tenant_domain_local_method"),
    )
    op.create_index("ix_tenant_domains_tenant_id", "tenant_domains", ["tenant_id"])
    op.execute("REVOKE ALL ON TABLE public.tenant_domains FROM platform_control_runtime")
    op.execute("GRANT SELECT, INSERT ON public.tenant_domains TO platform_control_runtime")
    op.execute(
        "GRANT UPDATE (verification_status, verified_at, updated_at) "
        "ON public.tenant_domains TO platform_control_runtime"
    )


def downgrade():
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
