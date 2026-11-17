"""Prevent duplicate tenant display names, ignoring case and outer spaces.

Revision ID: 002_unique_tenant_name
Revises: 001_tenant_registry
"""

from alembic import op

revision = "002_unique_tenant_name"
down_revision = "001_tenant_registry"
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL fails safely if existing names conflict; do not delete or merge data.
    op.execute(
        "CREATE UNIQUE INDEX uq_tenants_display_name_normalized "
        "ON public.tenants (lower(btrim(display_name)))"
    )


def downgrade():
    raise RuntimeError("Downgrade requires a separately reviewed migration")
