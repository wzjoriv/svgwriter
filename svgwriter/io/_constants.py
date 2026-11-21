"""
Constants for ``svgwriter.io``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CENTER_TOLERANCE",
    "CENTER_X",
    "CENTER_Y",
    "CHUNKS_PER_YIELD",
    "DEFAULT_ENCODING",
    "FOREIGN_PREFIX",
    "LEADING_ATTRIBUTES",
    "NAMESPACE_DECLARATION",
    "RANK",
]

CHUNKS_PER_YIELD: Final = 64

DEFAULT_ENCODING = "utf-8"
FOREIGN_PREFIX = "ns"
LEADING_ATTRIBUTES: Final = (
    "id", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "width", "height", "rx", "ry", "fx", "fy",
    "d", "points", "viewBox", "offset",
)
RANK: Final = {name: index for index, name in enumerate(LEADING_ATTRIBUTES)}

CENTER_X: Final = "inkscape:transform-center-x"
CENTER_Y: Final = "inkscape:transform-center-y"
CENTER_TOLERANCE: Final = 1e-9
NAMESPACE_DECLARATION: Final = "xmlns"
