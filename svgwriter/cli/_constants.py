"""
Constants for ``svgwriter.cli``: defaults, tables and patterns.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

__all__ = [
    "CANVAS_MARGIN",
    "DEFAULT_CANVAS",
    "DEFAULT_FONT",
    "DEFAULT_TEXT_SIZE",
    "DRAW_LAYOUTS",
    "EXIT_ERROR",
    "EXIT_FAILURE",
    "FRAME_FORMAT",
    "SIZE_COLUMN",
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

DRAW_LAYOUTS: Final[dict[str, Callable[[float, float], tuple[tuple[float, ...], dict[str, Any]]]]] = {
    "arrow": lambda c, r: ((c - r, c, c + r, c), {"line": True}),
    "regular_polygon": lambda c, r: ((c, c, r, 6), {}),
    "callout": lambda c, r: ((c - r, c - r, 2 * r, r), {"tail": (c - r / 2, c + r)}),
    "grid": lambda c, r: ((c - r, c - r, 2 * r, 2 * r), {"rows": 4, "cols": 4, "line": True}),
    "spiral": lambda c, r: ((c, c), {"turns": 3, "start_radius": 0, "end_radius": r, "line": True}),
    "wave": lambda c, r: ((c - r, c, 2 * r), {"amplitude": r / 3, "wavelength": r, "line": True}),
}
