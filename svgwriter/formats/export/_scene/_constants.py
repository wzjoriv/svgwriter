"""
Constants for the Excalidraw exporter and reader.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "ANCHORS", "ARROW_LENGTH", "ARROW_SPREAD", "ASCENT", "EXPORT_FAMILIES", "EXPORT_TOLERANCE", "FONTS",
    "LINE_HEIGHT",
    "OPACITY_SCALE", "ROUND_FRACTION", "ROUND_RADIUS", "SOURCE", "TRANSPARENT"
]

TRANSPARENT: Final = "transparent"
FONTS: Final = {1: "Virgil, Segoe Print, cursive", 2: "Helvetica, Arial, sans-serif",
                3: "Cascadia Code, Consolas, monospace", 5: "Excalifont, Segoe Print, cursive",
                6: "Nunito, Arial, sans-serif", 7: "Lilita One, Arial, sans-serif",
                8: "Comic Shanns, Comic Sans MS, cursive"}
ANCHORS: Final = {"left": "start", "center": "middle", "right": "end"}
ROUND_RADIUS: Final = 32.0
ROUND_FRACTION: Final = 0.25
LINE_HEIGHT: Final = 1.25
ASCENT: Final = 0.8
ARROW_LENGTH: Final = 15.0
ARROW_SPREAD: Final = 25.0
OPACITY_SCALE: Final = 100.0
EXPORT_TOLERANCE: Final = 0.1
SOURCE: Final = "svgwriter"
EXPORT_FAMILIES: Final = {"mono": 3, "consolas": 3, "courier": 3, "cursive": 1, "comic": 8}
