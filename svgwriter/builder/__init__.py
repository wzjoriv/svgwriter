"""Composite shapes (star, gear, heart, callout, wave, ...), effects (shadows, glows, markers) and presets.

Plain elements are built with the classes or their lowercase aliases (``svg.circle``); this module adds
what the element classes do not provide.
"""

from __future__ import annotations

from ._effects import arrow_marker, drawing, drop_shadow, glow
from ._functions import dashed_line, dot, outline
from ._lines import grid, spiral, wave
from ._shapes import SHAPES, arrow, gear, regular_polygon, shape_factory, star
from ._symbols import callout, cross, heart

__all__ = [
    "SHAPES",
    "arrow",
    "arrow_marker",
    "callout",
    "cross",
    "dashed_line",
    "dot",
    "drawing",
    "drop_shadow",
    "gear",
    "glow",
    "grid",
    "heart",
    "outline",
    "regular_polygon",
    "shape_factory",
    "spiral",
    "star",
    "wave",
]
