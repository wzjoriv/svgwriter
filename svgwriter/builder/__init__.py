"""Composite shapes (star, gear, arrow, ...), effects (shadows, glows, markers) and presets.

Plain elements are built with the classes or their lowercase aliases (``svg.circle``); this module adds
what the element classes do not provide.
"""

from __future__ import annotations

from ._effects import arrow_marker, drawing, drop_shadow, glow
from ._functions import dashed_line, dot, outline
from ._shapes import SHAPES, arrow, gear, shape_factory, star

__all__ = [
    "SHAPES",
    "arrow",
    "arrow_marker",
    "dashed_line",
    "dot",
    "drawing",
    "drop_shadow",
    "gear",
    "glow",
    "outline",
    "shape_factory",
    "star",
]
