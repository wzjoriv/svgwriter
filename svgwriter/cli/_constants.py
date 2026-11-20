"""
Constants for ``svgwriter.cli``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CANVAS_MARGIN",
    "DEFAULT_CANVAS",
    "DEFAULT_FONT",
    "DEFAULT_TEXT_SIZE",
    "EXIT_FAILURE",
    "SCENE_DOCUMENTS",
    "SCENE_FACTORIES",
    "STROKE_WIDTH",
    "TEXT_MARGIN",
]

DEFAULT_CANVAS: Final = 200.0
CANVAS_MARGIN: Final = 0.4
STROKE_WIDTH: Final = 2

SCENE_FACTORIES: Final = ("build", "scene")
SCENE_DOCUMENTS: Final = ("document", "doc")
EXIT_FAILURE: Final = 1
DEFAULT_TEXT_SIZE: Final = 48.0
DEFAULT_FONT: Final = "sans-serif"
TEXT_MARGIN: Final = 4.0
