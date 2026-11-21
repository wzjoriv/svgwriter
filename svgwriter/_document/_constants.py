"""
Constants for ``svgwriter._document``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "BUILTIN_SIZES",
    "INLINE_STYLE",
    "LANDSCAPE_SUFFIX",
    "PORTRAIT_SUFFIX",
    "RASTER_REPRS",
]

RASTER_REPRS: Final = ("_repr_png_", "_repr_jpeg_")

INLINE_STYLE: Final = "display:inline-block;max-width:100%;overflow:auto;line-height:0"

LANDSCAPE_SUFFIX: Final = "-landscape"
PORTRAIT_SUFFIX: Final = "-portrait"

BUILTIN_SIZES: Final = {
    "a0": ("841mm", "1189mm"),
    "a1": ("594mm", "841mm"),
    "a2": ("420mm", "594mm"),
    "a3": ("297mm", "420mm"),
    "a4": ("210mm", "297mm"),
    "a5": ("148mm", "210mm"),
    "a6": ("105mm", "148mm"),
    "letter": ("8.5in", "11in"),
    "legal": ("8.5in", "14in"),
    "tabloid": ("11in", "17in"),
    "business-card": ("3.5in", "2in"),
    "slide-16:9": (1280, 720),
    "slide-4:3": (960, 720),
    "video-720p": (1280, 720),
    "video-1080p": (1920, 1080),
    "instagram-post": (1080, 1080),
    "instagram-portrait": (1080, 1350),
    "instagram-story": (1080, 1920),
    "og-image": (1200, 630),
    "youtube-thumbnail": (1280, 720),
    "favicon": (32, 32),
    "apple-touch-icon": (180, 180),
    "icon": (512, 512),
}
