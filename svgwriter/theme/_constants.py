"""
Constants for ``svgwriter.theme``: built-in palettes, fonts, role measures and file syntax.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "BORDER_MIX",
    "BUILTIN_PALETTES",
    "DEFAULT_THEME",
    "FILE_FONT_KEYS",
    "FILE_KEYS",
    "FONT_FAMILY",
    "FONT_SIZES",
    "FONT_WEIGHTS",
    "LENGTH_PROPERTIES",
    "LINE_WIDTH",
    "MONOSPACE_FAMILY",
    "MUTED_MIX",
    "OPACITY_PROPERTIES",
    "REFERENCE_RE",
    "ROLE_CLASS_PREFIX",
    "ROLE_NAME_RE",
    "STYLE_ID",
    "THIN_LINE_WIDTH",
    "TOML_BARE_KEY_RE",
]

DEFAULT_THEME: Final = "light"
ROLE_CLASS_PREFIX: Final = "role-"
STYLE_ID: Final = "svgwriter-theme"
ROLE_NAME_RE: Final = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*")
REFERENCE_RE: Final = re.compile(r"\{([a-z_][a-z0-9_]*(?:\.[a-z0-9_]+)+)\}")
FILE_KEYS: Final = frozenset({"name", "extends", "palette", "fonts", "roles"})
FILE_FONT_KEYS: Final = frozenset({"family", "monospace", "sizes", "weights"})
TOML_BARE_KEY_RE: Final = re.compile(r"[A-Za-z0-9_-]+")

FONT_FAMILY: Final = "Helvetica, Arial, sans-serif"
MONOSPACE_FAMILY: Final = "Consolas, Menlo, monospace"
FONT_SIZES: Final = {"text": 14.0, "title": 24.0, "subtitle": 18.0, "caption": 11.0}
FONT_WEIGHTS: Final = {"regular": 400, "bold": 700}

LENGTH_PROPERTIES: Final = frozenset({"font-size", "stroke-width", "stroke-dashoffset"})
OPACITY_PROPERTIES: Final = {"fill": "fill-opacity", "stroke": "stroke-opacity", "stop-color": "stop-opacity",
                              "flood-color": "flood-opacity"}
LINE_WIDTH: Final = 2.0
THIN_LINE_WIDTH: Final = 1.0
BORDER_MIX: Final = 0.7
MUTED_MIX: Final = 0.45

BUILTIN_PALETTES: Final = {
    "light": {
        "background": "#ffffff", "foreground": "#1f2933", "surface": "#f4f6f8",
        "primary": "#0f766e", "on_primary": "#ffffff", "secondary": "#4f46e5", "accent": "#fbbf24",
        "success": "#15803d", "warning": "#b45309", "error": "#b91c1c",
    },
    "dark": {
        "background": "#111827", "foreground": "#e5e7eb", "surface": "#1f2937",
        "primary": "#99f6e4", "on_primary": "#042f2e", "secondary": "#a5b4fc", "accent": "#b45309",
        "success": "#4ade80", "warning": "#fbbf24", "error": "#f87171",
    },
    "paper": {
        "background": "#fbf7ef", "foreground": "#3b3128", "surface": "#f3ecdf",
        "primary": "#8c4a2f", "on_primary": "#fbf7ef", "secondary": "#4a6670", "accent": "#c08a2d",
        "success": "#4d7c3a", "warning": "#b7791f", "error": "#9b2c2c",
    },
    "print": {
        "background": "#ffffff", "foreground": "#000000", "surface": "#ffffff",
        "primary": "#08306b", "on_primary": "#ffffff", "secondary": "#a50f15", "accent": "#cc6600",
        "success": "#006d2c", "warning": "#cc6600", "error": "#a50f15",
    },
    "mono": {
        "background": "#ffffff", "foreground": "#000000", "surface": "#ffffff",
        "primary": "#000000", "on_primary": "#ffffff", "secondary": "#000000", "accent": "#000000",
        "success": "#000000", "warning": "#000000", "error": "#000000",
    },
}
