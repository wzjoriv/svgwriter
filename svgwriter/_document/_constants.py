"""
Constants for ``svgwriter._document``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "INLINE_STYLE",
    "RASTER_REPRS",
]

RASTER_REPRS: Final = ("_repr_png_", "_repr_jpeg_")

INLINE_STYLE: Final = "display:inline-block;max-width:100%;overflow:auto;line-height:0"
