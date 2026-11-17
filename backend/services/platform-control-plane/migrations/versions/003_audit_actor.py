"""Record trusted operator identity for tenant audit events."""

import sqlalchemy as sa
from alembic import op

revision = "003_audit_actor"
down_revision = "002_unique_tenant_name"
branch_labels = None
depends_on = None


def upgrade():
    # Existing events have no trustworthy actor and remain NULL.
    op.add_column("tenant_audit_events", sa.Column("actor_issuer", sa.String(512), nullable=True))
    op.add_column("tenant_audit_events", sa.Column("actor_subject", sa.String(255), nullable=True))


def downgrade():
    raise RuntimeError("Downgrade requires a separately reviewed migration")
