"""
Constants for ``svgwriter.catalog.fonts``: default metrics, code points, formats and cheatsheet layout.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CHEAT_CELL",
    "CHEAT_COLUMNS",
    "CHEAT_GAP",
    "CHEAT_GLYPH",
    "CHEAT_LABEL",
    "CHEAT_LABEL_SIZE",
    "CHEAT_MUTED",
    "CHEAT_STROKE",
    "CSS_FORMATS",
    "CUBIC_TO_QUADRATIC_ERROR",
    "DEFAULT_ASCENT",
    "DEFAULT_CAP_HEIGHT",
    "DEFAULT_DESCENT",
    "DEFAULT_FAMILY",
    "DEFAULT_ICON_PREFIX",
    "DEFAULT_STYLE",
    "DEFAULT_UNITS_PER_EM",
    "DEFAULT_VERSION",
    "DEFAULT_WEIGHT",
    "DEFAULT_X_HEIGHT",
    "FONT_FORMATS",
    "FS_ITALIC",
    "FS_REGULAR",
    "ITALIC_STYLES",
    "MAC_ITALIC",
    "NOTDEF",
    "NOTDEF_INSET",
    "NOTDEF_WIDTH",
    "OS2_VERSION",
    "PRIVATE_USE_END",
    "PRIVATE_USE_START",
    "SPACE",
    "SPACE_WIDTH",
    "TRUETYPE_FORMATS",
    "USE_TYPO_METRICS",
    "WEB_FLAVORS",
]

DEFAULT_FAMILY: Final = "Untitled"
DEFAULT_STYLE: Final = "Regular"
DEFAULT_WEIGHT: Final = 400
DEFAULT_UNITS_PER_EM: Final = 1000
DEFAULT_ASCENT: Final = 800
DEFAULT_DESCENT: Final = 200
DEFAULT_CAP_HEIGHT: Final = 700
DEFAULT_X_HEIGHT: Final = 500
DEFAULT_VERSION: Final = "1.000"
DEFAULT_ICON_PREFIX: Final = "icon"

PRIVATE_USE_START: Final = 0xE000
PRIVATE_USE_END: Final = 0xF8FF

NOTDEF: Final = ".notdef"
NOTDEF_WIDTH: Final = 0.5
NOTDEF_INSET: Final = 0.05
SPACE: Final = " "
SPACE_WIDTH: Final = 0.25

ITALIC_STYLES: Final = frozenset({"italic", "oblique", "bold italic", "bold oblique"})
OS2_VERSION: Final = 4
USE_TYPO_METRICS: Final = 1 << 7
FS_ITALIC: Final = 1
FS_REGULAR: Final = 1 << 6
MAC_ITALIC: Final = 1 << 1
CUBIC_TO_QUADRATIC_ERROR: Final = 1.0

FONT_FORMATS: Final = ("otf", "ttf", "woff", "woff2")
TRUETYPE_FORMATS: Final = frozenset({"ttf"})
WEB_FLAVORS: Final = frozenset({"woff", "woff2"})
CSS_FORMATS: Final = {"otf": "opentype", "ttf": "truetype", "woff": "woff", "woff2": "woff2"}

CHEAT_COLUMNS: Final = 6
CHEAT_CELL: Final = 120
CHEAT_GAP: Final = 12
CHEAT_GLYPH: Final = 0.55
CHEAT_LABEL: Final = 30
CHEAT_LABEL_SIZE: Final = 11
CHEAT_MUTED: Final = "#64748b"
CHEAT_STROKE: Final = "#cbd5e1"
