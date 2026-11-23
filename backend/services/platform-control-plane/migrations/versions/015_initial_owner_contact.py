"""Store the initial tenant-owner contact for Identity bootstrap."""

import sqlalchemy as sa
from alembic import op

revision = "015_owner_contact"
down_revision = "014_identity_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("initial_owner_email", sa.String(320), nullable=True))
    op.create_check_constraint(
        "ck_tenant_initial_owner_email_normalized",
        "tenants",
        "initial_owner_email IS NULL OR ("
        "initial_owner_email = lower(btrim(initial_owner_email)) "
        "AND initial_owner_email !~ '[[:space:]]' "
        "AND length(initial_owner_email) BETWEEN 3 AND 320)",
    )
    op.execute("REVOKE INSERT ON TABLE tenants FROM platform_control_runtime")
    op.execute(
        "GRANT INSERT (id, display_name, initial_owner_email) "
        "ON TABLE tenants TO platform_control_runtime"
    )
    op.execute(
        "GRANT UPDATE (initial_owner_email, updated_at) "
        "ON TABLE tenants TO platform_control_runtime"
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
