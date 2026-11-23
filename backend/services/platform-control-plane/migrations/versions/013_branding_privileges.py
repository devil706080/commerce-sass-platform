"""Restrict runtime tenant-branding writes to required columns."""

from alembic import op

revision = "013_branding_privileges"
down_revision = "012_tenant_branding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("REVOKE INSERT, UPDATE ON TABLE tenant_branding FROM platform_control_runtime")
    op.execute(
        "GRANT INSERT (tenant_id, display_name, fallback_initials, theme_key) "
        "ON TABLE tenant_branding TO platform_control_runtime"
    )
    op.execute(
        "GRANT UPDATE (display_name, fallback_initials, theme_key, updated_at) "
        "ON TABLE tenant_branding TO platform_control_runtime"
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
