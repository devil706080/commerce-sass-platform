from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from platform_control_plane.core.themes import THEMES

ThemeKey = Literal["ocean_teal", "emerald", "indigo", "berry", "amber"]


class BrandingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=120)
    fallback_initials: str | None = Field(default=None, min_length=1, max_length=4)
    theme_key: ThemeKey = "ocean_teal"

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display name must not be blank")
        return value

    @field_validator("fallback_initials")
    @classmethod
    def normalize_initials(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = "".join(
            character for character in value.upper() if character.isascii() and character.isalnum()
        )
        if not normalized:
            raise ValueError("initials must contain ASCII letters or numbers")
        return normalized[:4]


class ThemeResponse(BaseModel):
    key: ThemeKey
    name: str
    primary: str
    primary_dark: str
    accent: str
    surface: str


class BrandingResponse(BaseModel):
    tenant_id: UUID
    display_name: str
    fallback_initials: str
    theme_key: ThemeKey
    logo_media_id: UUID | None
    palette: dict[str, str]
    created_at: datetime
    updated_at: datetime


def generated_initials(name: str) -> str:
    words = [
        "".join(
            character for character in word.upper() if character.isascii() and character.isalnum()
        )
        for word in name.split()
    ]
    words = [word for word in words if word]
    if not words:
        return "NA"
    return "".join(word[0] for word in words[:2]) if len(words) > 1 else words[0][:2]


def palette(theme_key: ThemeKey) -> dict[str, str]:
    theme = THEMES[theme_key]
    return {
        "primary": theme["primary"],
        "primary_dark": theme["primary_dark"],
        "accent": theme["accent"],
        "surface": theme["surface"],
    }
