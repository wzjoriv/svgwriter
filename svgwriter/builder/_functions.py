"""
Small conveniences: styled presets of the basic shapes.
"""

from __future__ import annotations

from functools import partial
from typing import Final

from ..elements.shapes import Circle, Line, Rect

__all__ = ["dashed_line", "dot", "outline"]

DASH_PATTERN: Final = (4, 2)
DOT_RADIUS: Final = 2

outline = partial(Rect, fill="none", stroke="black")
"""``outline(x, y, width, height, **kwargs)``: an unfilled black-stroked rectangle."""
dashed_line = partial(Line, stroke="black", stroke_dasharray=DASH_PATTERN)
"""``dashed_line(x1, y1, x2, y2, **kwargs)``: a black dashed line."""
dot = partial(Circle, r=DOT_RADIUS)
"""``dot(cx, cy, **kwargs)``: a small filled circle."""
