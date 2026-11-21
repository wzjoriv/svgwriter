"""
Constants for ``svgwriter.catalog.markers``: the drawing box, default size and shape proportions.
"""

from __future__ import annotations

from typing import Final

__all__ = ["BAR_WIDTH", "BOX", "CHEVRON_WIDTH", "FALLBACK_INK", "MARKER_SIZE", "ROLE"]

BOX: Final = 10.0
MARKER_SIZE: Final = 5.0
BAR_WIDTH: Final = 2.0
CHEVRON_WIDTH: Final = 2.5
ROLE: Final = "arrow.head"
FALLBACK_INK: Final = "black"
