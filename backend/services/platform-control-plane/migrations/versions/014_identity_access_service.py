"""Allow Identity & Access tenant infrastructure provisioning."""

from alembic import op

revision = "014_identity_access"
down_revision = "013_branding_privileges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_provisioning_service_key", "provisioning_jobs", type_="check")
    op.create_check_constraint(
        "ck_provisioning_service_key",
        "provisioning_jobs",
        "service_key IN "
        "('catalogue_fixture', 'inventory_fixture', 'media_fixture', 'identity_access')",
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
