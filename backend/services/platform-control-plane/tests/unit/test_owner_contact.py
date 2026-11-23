import pytest
from pydantic import ValidationError

from platform_control_plane.schemas.tenant import TenantCreate, TenantOwnerContactUpdate


def test_owner_email_is_validated_and_normalized() -> None:
    tenant = TenantCreate(
        display_name="Example",
        initial_owner_email="  Owner@Example.COM ",
    )
    update = TenantOwnerContactUpdate(initial_owner_email="ADMIN@EXAMPLE.COM")

    assert tenant.initial_owner_email == "owner@example.com"
    assert update.initial_owner_email == "admin@example.com"


@pytest.mark.parametrize("email", ["invalid", "@example.com", "owner@", "owner @example.com"])
def test_invalid_owner_email_is_rejected(email: str) -> None:
    with pytest.raises(ValidationError):
        TenantCreate(display_name="Example", initial_owner_email=email)
