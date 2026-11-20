"""
Constants for ``svgwriter.builder``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ARROW_HEAD_ANGLE",
    "DASH_PATTERN",
    "DEFAULT_BLUR",
    "DEFAULT_HEAD_SIZE",
    "DEFAULT_INNER_RATIO",
    "DEFAULT_SHADOW_OFFSET",
    "DEFAULT_SHADOW_OPACITY",
    "DEFAULT_STAR_POINTS",
    "DEFAULT_TEETH",
    "DOT_RADIUS",
    "FILTER_EXTENT",
    "FILTER_MARGIN",
    "FULL_TURN",
    "MARKER_SIZE",
    "QUARTER_TURN",
    "TOOTH_DEPTH_RATIO",
]

DEFAULT_SHADOW_OFFSET: Final = 2.0
DEFAULT_BLUR: Final = 2.0
DEFAULT_SHADOW_OPACITY: Final = 0.5
FILTER_MARGIN: Final = "-20%"
FILTER_EXTENT: Final = "140%"
MARKER_SIZE: Final = 10.0

DASH_PATTERN: Final = (4, 2)
DOT_RADIUS: Final = 2

FULL_TURN: Final = 360.0

QUARTER_TURN: Final = 90.0
DEFAULT_STAR_POINTS: Final = 5
DEFAULT_INNER_RATIO: Final = 0.5
DEFAULT_HEAD_SIZE: Final = 10.0
ARROW_HEAD_ANGLE: Final = 30.0
DEFAULT_TEETH: Final = 12
TOOTH_DEPTH_RATIO: Final = 0.15
