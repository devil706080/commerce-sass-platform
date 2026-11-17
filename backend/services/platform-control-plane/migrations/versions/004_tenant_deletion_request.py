"""Add the audited tenant deletion-request lifecycle state."""

from alembic import op

revision = "004_tenant_deletion_request"
down_revision = "003_audit_actor"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_tenant_pending", "tenants", type_="check")
    op.create_check_constraint(
        "ck_tenant_status",
        "tenants",
        "status IN ('PENDING', 'DELETION_REQUESTED')",
    )
    op.execute("GRANT UPDATE (status, updated_at) ON public.tenants TO platform_control_runtime")


def downgrade():
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
