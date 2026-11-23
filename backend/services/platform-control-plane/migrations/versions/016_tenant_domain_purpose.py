"""Classify tenant domains by application purpose."""

import sqlalchemy as sa
from alembic import op

revision = "016_domain_purpose"
down_revision = "015_owner_contact"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant_domains",
        sa.Column("purpose", sa.String(24), nullable=False, server_default="STOREFRONT"),
    )
    op.create_check_constraint(
        "ck_tenant_domain_purpose",
        "tenant_domains",
        "purpose IN ('STOREFRONT', 'TENANT_ADMIN')",
    )
    op.create_unique_constraint(
        "uq_tenant_domain_purpose",
        "tenant_domains",
        ["tenant_id", "purpose"],
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
