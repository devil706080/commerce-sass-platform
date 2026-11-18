"""Allow Media to be provisioned as a tenant-scoped service."""

from alembic import op

revision = "011_media_service"
down_revision = "010_active_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_provisioning_service_key", "provisioning_jobs", type_="check")
    op.create_check_constraint(
        "ck_provisioning_service_key",
        "provisioning_jobs",
        "service_key IN ('catalogue_fixture', 'inventory_fixture', 'media_fixture')",
    )


def downgrade() -> None:
    raise RuntimeError("Downgrade requires a separately reviewed recovery migration")
