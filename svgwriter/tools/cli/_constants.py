"""
Constants for ``svgwriter.tools.cli``: defaults, tables and patterns.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

__all__ = [
    "CANVAS_MARGIN",
    "COMMON_SIZES",
    "CUSTOM_SIZE",
    "DEFAULT_CANVAS",
    "DEFAULT_FONT",
    "DEFAULT_TEXT_SIZE",
    "DOCTOR_COLUMNS",
    "DOCTOR_FEW_FAMILIES",
    "DOCTOR_MARKS",
    "DRAW_LAYOUTS",
    "EXIT_ERROR",
    "EXIT_FAILURE",
    "DEFAULT_PRESET",
    "FRAME_FORMAT",
    "JSON_INDENT",
    "KEEP_CHOICE",
    "PRESET_COLUMN",
    "SIZE_COLUMN",
    "SIZE_SEPARATOR",
    "STROKE_WIDTH",
    "TEXT_MARGIN",
]

DEFAULT_CANVAS: Final = 200.0
CANVAS_MARGIN: Final = 0.4
STROKE_WIDTH: Final = 2

FRAME_FORMAT: Final = "png"
EXIT_FAILURE: Final = 1
EXIT_ERROR: Final = 2
DEFAULT_TEXT_SIZE: Final = 48.0
DEFAULT_FONT: Final = "sans-serif"
TEXT_MARGIN: Final = 4.0
SIZE_COLUMN: Final = 20
PRESET_COLUMN: Final = 12
DEFAULT_PRESET: Final = "blank"
SIZE_SEPARATOR: Final = ","
DOCTOR_COLUMNS: Final = (12, 60)
"""Width of the capability name column and the longest version shown by ``doctor``."""
DOCTOR_MARKS: Final = {True: "ok  ", False: "--  "}
DOCTOR_FEW_FAMILIES: Final = 10
"""Below this many installed families, ``doctor`` suggests the distribution's font packages."""
JSON_INDENT: Final = 2
KEEP_CHOICE: Final = "the preset's own"
CUSTOM_SIZE: Final = "custom width and height"
COMMON_SIZES: Final = ("a4", "a3", "a5", "letter", "slide-16:9", "slide-4:3", "video-1080p", "instagram-post",
                       "og-image", "icon")
"""Named sizes the arrow-key prompt lists first; ``svgwriter sizes`` has them all."""

DRAW_LAYOUTS: Final[dict[str, Callable[[float, float], tuple[tuple[float, ...], dict[str, Any]]]]] = {
    "arrow": lambda c, r: ((c - r, c, c + r, c), {"line": True}),
    "regular_polygon": lambda c, r: ((c, c, r, 6), {}),
    "callout": lambda c, r: ((c - r, c - r, 2 * r, r), {"tail": (c - r / 2, c + r)}),
    "grid": lambda c, r: ((c - r, c - r, 2 * r, 2 * r), {"rows": 4, "cols": 4, "line": True}),
    "spiral": lambda c, r: ((c, c), {"turns": 3, "start_radius": 0, "end_radius": r, "line": True}),
    "wave": lambda c, r: ((c - r, c, 2 * r), {"amplitude": r / 3, "wavelength": r, "line": True}),
}
