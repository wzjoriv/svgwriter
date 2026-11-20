"""
Constants for ``svgwriter.builder``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ARROW_HEAD_ANGLE",
    "BLINK_VALUES",
    "BOUNCE_HEIGHT",
    "BOUNCE_TIMES",
    "BOUNCE_VALUES",
    "DASH_PATTERN",
    "DEFAULT_BLUR",
    "DEFAULT_DURATION",
    "DEFAULT_HEAD_SIZE",
    "DEFAULT_INNER_RATIO",
    "DEFAULT_SHADOW_OFFSET",
    "DEFAULT_SHADOW_OPACITY",
    "DEFAULT_STAR_POINTS",
    "DEFAULT_TEETH",
    "DOT_RADIUS",
    "FILTER_EXTENT",
    "FILTER_MARGIN",
    "FOREVER",
    "FULL_TURN",
    "MARKER_SIZE",
    "PULSE_SCALE",
    "QUARTER_TURN",
    "SHAKE_DISTANCE",
    "SHAKE_STEPS",
    "SIDES",
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

DEFAULT_DURATION: Final = 1.0
FOREVER: Final = "indefinite"
FULL_TURN: Final = 360.0
PULSE_SCALE: Final = 1.1
SHAKE_DISTANCE: Final = 4.0
SHAKE_STEPS: Final = 6
BOUNCE_HEIGHT: Final = 20.0
BOUNCE_VALUES: Final = (0.0, 1.0, 0.0, 0.45, 0.0, 0.15, 0.0)
BOUNCE_TIMES: Final = (0.0, 0.25, 0.5, 0.65, 0.8, 0.9, 1.0)
BLINK_VALUES: Final = "1;0;1"
SIDES: Final = {"left": (-1.0, 0.0), "right": (1.0, 0.0), "top": (0.0, -1.0), "bottom": (0.0, 1.0)}

QUARTER_TURN: Final = 90.0
DEFAULT_STAR_POINTS: Final = 5
DEFAULT_INNER_RATIO: Final = 0.5
DEFAULT_HEAD_SIZE: Final = 10.0
ARROW_HEAD_ANGLE: Final = 30.0
DEFAULT_TEETH: Final = 12
TOOTH_DEPTH_RATIO: Final = 0.15
