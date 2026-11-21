"""
Filter-effect engine: filter regions, the primitive graph, inputs, lighting and image effects.
"""

from __future__ import annotations

from ._filtered import draw_filtered, needs_engine
from ._image_effects import paint_mask

__all__ = [
    "draw_filtered",
    "needs_engine",
    "paint_mask",
]
