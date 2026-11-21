"""Geometry backed by skia: boolean operations, measurement, text outlines.

The same features are reachable from elements: ``a | b``,
``a & b``, ``a - b``, ``a ^ b``, ``shape.total_length()``,
``shape.contains_point(x, y)`` and so on.

Example
-------
>>> import svgwriter as svg
>>> from svgwriter import ops
>>> ring = svg.Circle(50, 50, 40) - svg.Circle(50, 50, 20)
>>> ops.contains(ring, 50, 50)
False
"""

from __future__ import annotations

from ._skia import Geometry, from_skia, to_skia
from .boolean import BooleanOp, combine, difference, intersection, simplify, union, xor
from .composite import Operator, composite_rgba, resolve_operator
from .graph import draw_graph
from .interpolate import interpolate, register_interpolator, unregister_interpolator
from .measure import (
    Cap,
    Join,
    bounds,
    contains,
    point_at_length,
    stroke_to_path,
    tangent_at_length,
    total_length,
)
from .parallel import rasterize_many
from .plot import to_matplotlib
from .render import encode, rasterize, render_frame, render_png, render_svg
from .text import Anchor, FontWeight, register_font, text_outline, text_to_path, text_width

__all__ = [
    "Anchor",
    "BooleanOp",
    "Cap",
    "FontWeight",
    "Geometry",
    "Join",
    "Operator",
    "bounds",
    "combine",
    "composite_rgba",
    "contains",
    "difference",
    "draw_graph",
    "from_skia",
    "interpolate",
    "intersection",
    "point_at_length",
    "encode",
    "rasterize",
    "rasterize_many",
    "render_png",
    "register_font",
    "register_interpolator",
    "render_svg",
    "resolve_operator",
    "simplify",
    "render_frame",
    "stroke_to_path",
    "tangent_at_length",
    "text_outline",
    "text_to_path",
    "unregister_interpolator",
    "text_width",
    "to_matplotlib",
    "to_skia",
    "total_length",
    "union",
    "xor",
]
