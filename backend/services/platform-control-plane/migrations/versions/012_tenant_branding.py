"""Add centrally managed tenant branding."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "012_tenant_branding"
down_revision = "011_media_service"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_branding",
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("fallback_initials", sa.String(4), nullable=False),
        sa.Column("theme_key", sa.String(32), nullable=False, server_default="ocean_teal"),
        sa.Column("logo_media_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("fallback_initials ~ '^[A-Z0-9]{1,4}$'", name="ck_branding_initials"),
        sa.CheckConstraint(
            "theme_key IN ('ocean_teal','emerald','indigo','berry','amber')",
            name="ck_branding_theme",
        ),
    )
    op.execute(
        "INSERT INTO tenant_branding (tenant_id,display_name,fallback_initials,theme_key) "
        "SELECT id,display_name,upper(left(split_part(btrim(display_name),' ',1),1) || "
        "CASE WHEN position(' ' in btrim(display_name)) > 0 THEN left(regexp_replace(btrim(display_name), '^.*\\s', ''),1) "
        "ELSE substring(btrim(display_name),2,1) END),'ocean_teal' FROM tenants"
    )
    op.execute("REVOKE ALL ON TABLE tenant_branding FROM platform_control_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE ON TABLE tenant_branding TO platform_control_runtime")


def downgrade() -> None:
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
