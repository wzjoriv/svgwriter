"""
Raster painting: the canvas, paint layers, element painting and native text drawing.
"""

from __future__ import annotations

from ._canvas import make_surface, paint_svg, read_pixels
from ._layers import concealed, draw_image, hidden, referenced, skia_matrix
from ._painting import paint_tree, render_tree

__all__ = [
    "concealed",
    "draw_image",
    "hidden",
    "make_surface",
    "paint_svg",
    "paint_tree",
    "read_pixels",
    "referenced",
    "render_tree",
    "skia_matrix",
]
