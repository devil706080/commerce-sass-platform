from typing import Final, TypedDict


class ThemeDefinition(TypedDict):
    name: str
    primary: str
    primary_dark: str
    accent: str
    surface: str


THEMES: Final[dict[str, ThemeDefinition]] = {
    "ocean_teal": {
        "name": "Ocean Teal",
        "primary": "#0969B8",
        "primary_dark": "#064A87",
        "accent": "#12B889",
        "surface": "#F3F9FC",
    },
    "emerald": {
        "name": "Emerald",
        "primary": "#167A62",
        "primary_dark": "#0E5948",
        "accent": "#D89B2B",
        "surface": "#F1F9F5",
    },
    "indigo": {
        "name": "Indigo",
        "primary": "#5756B3",
        "primary_dark": "#393878",
        "accent": "#16A6A1",
        "surface": "#F5F4FC",
    },
    "berry": {
        "name": "Berry",
        "primary": "#A33B71",
        "primary_dark": "#70264D",
        "accent": "#E57B59",
        "surface": "#FCF3F7",
    },
    "amber": {
        "name": "Amber",
        "primary": "#B85E1C",
        "primary_dark": "#7D3D12",
        "accent": "#167C80",
        "surface": "#FCF6F0",
    },
}
