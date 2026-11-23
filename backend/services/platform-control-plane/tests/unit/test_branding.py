import pytest
from pydantic import ValidationError

from platform_control_plane.core.themes import THEMES
from platform_control_plane.schemas.branding import BrandingInput, generated_initials, palette


def test_exactly_five_curated_light_themes_are_available():
    assert list(THEMES) == ["ocean_teal", "emerald", "indigo", "berry", "amber"]
    assert all(theme["primary"].startswith("#") for theme in THEMES.values())


def test_branding_input_normalizes_operator_values():
    branding = BrandingInput(
        display_name="  Lifemac Pharma  ",
        fallback_initials="l-p!",
        theme_key="ocean_teal",
    )
    assert branding.display_name == "Lifemac Pharma"
    assert branding.fallback_initials == "LP"


def test_branding_rejects_unknown_theme_and_non_ascii_initials():
    with pytest.raises(ValidationError):
        BrandingInput(display_name="Lifemac", theme_key="dark")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        BrandingInput(display_name="Lifemac", fallback_initials="é")


def test_initials_and_palette_are_deterministic():
    assert generated_initials("Lifemac Pharma") == "LP"
    assert generated_initials("Acme") == "AC"
    assert generated_initials("---") == "NA"
    assert palette("ocean_teal") == {
        "primary": "#0969B8",
        "primary_dark": "#064A87",
        "accent": "#12B889",
        "surface": "#F3F9FC",
    }
