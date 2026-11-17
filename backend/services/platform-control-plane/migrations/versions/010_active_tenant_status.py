"""Allow fully verified tenants to become active."""

from alembic import op

revision = "010_active_status"
down_revision = "009_service_ready"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_tenant_status", "tenants", type_="check")
    op.create_check_constraint(
        "ck_tenant_status",
        "tenants",
        "status IN ('PENDING','PROVISIONING','FAILED','ACTIVE','DELETION_REQUESTED')",
    )


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed recovery migration")
