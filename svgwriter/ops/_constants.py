"""
Constants for ``svgwriter.ops``: defaults, tables and patterns.
"""

from __future__ import annotations

from typing import Final

import skia

__all__ = [
    "ALPHA_ONLY",
    "ANCHOR_SHIFT",
    "ARITHMETIC_TERMS",
    "ARROW_LENGTH",
    "ARROW_SPREAD",
    "BLEND",
    "BOLD_WEIGHT",
    "CAPS",
    "CHANNEL_MAX",
    "CHANNEL_SCALE",
    "CJK_START",
    "CLOSEPOLY",
    "COMPLEX_SCRIPT_START",
    "COMPOSITE",
    "CONIC_SUBDIVISION",
    "CONTAINERS",
    "CURVE4",
    "DEFAULT_FAMILY",
    "DEFAULT_FONT_SIZE",
    "DEFAULT_MITER_LIMIT",
    "DEFAULT_QUALITY",
    "DEFAULT_STROKE_WIDTH",
    "DISCRETE_SWITCH",
    "DISPLAY",
    "EDGE_STROKE",
    "EDGE_WIDTH",
    "EFFECTS",
    "EMOJI_START",
    "EVENODD",
    "EXTRA_HINT",
    "FONT_CACHE",
    "FORMATS",
    "FULL_TURN",
    "GENERIC_CANDIDATES",
    "GENERIC_FAMILIES",
    "GEOMETRY_SKIP",
    "GLYPH_CACHE",
    "GRAPH_SIZE",
    "HALF_TURN",
    "JOINS",
    "LABEL_SIZE",
    "LATIN_EXTENDED_ADDITIONAL",
    "LAYOUTS",
    "LINETO",
    "LINK_CACHE",
    "LUMA",
    "MARGIN",
    "MASK_CANVAS",
    "MEASURE_PRECISION",
    "MISSING_GLYPH",
    "MOVETO",
    "NODE_FILL",
    "NODE_RADIUS",
    "NODE_STROKE",
    "NORMAL_WEIGHT",
    "NORMAL_WIDTH",
    "NOT_RENDERED",
    "NO_DECORATION",
    "PIXEL_EPSILON",
    "POINTS_PER_UNIT",
    "POSITION_TOLERANCE",
    "SERIAL_LIMIT",
    "SOURCE_ALPHA",
    "SOURCE_GRAPHIC",
]

SOURCE_GRAPHIC: Final = "SourceGraphic"
SOURCE_ALPHA: Final = "SourceAlpha"
ALPHA_ONLY: Final = [0.0] * 15 + [0.0, 0.0, 0.0, 1.0, 0.0]
LUMA: Final = (0.2125, 0.7154, 0.0721)
BLEND: Final = {"normal": skia.BlendMode.kSrcOver, "multiply": skia.BlendMode.kMultiply,
                "screen": skia.BlendMode.kScreen, "darken": skia.BlendMode.kDarken,
                "lighten": skia.BlendMode.kLighten}
COMPOSITE: Final = {"over": skia.BlendMode.kSrcOver, "in": skia.BlendMode.kSrcIn, "out": skia.BlendMode.kSrcOut,
                    "atop": skia.BlendMode.kSrcATop, "xor": skia.BlendMode.kXor}
MASK_CANVAS: Final = 1e6

NOT_RENDERED: Final = frozenset({"defs", "clipPath", "mask", "pattern", "marker", "symbol", "linearGradient",
                                 "radialGradient", "filter", "title", "desc", "metadata", "style", "font",
                                 "font-face", "glyph", "missing-glyph"})
CONTAINERS: Final = frozenset({"svg", "g", "a", "switch"})
CHANNEL_MAX: Final = 255
LINK_CACHE: Final = 64

EFFECTS: Final = ("filter", "mask")
NO_DECORATION: Final = ("", "none")
DEFAULT_FONT_SIZE: Final = 16.0
MISSING_GLYPH: Final = 0
POSITION_TOLERANCE: Final = 0.01

CONIC_SUBDIVISION: Final = 3
EVENODD: Final = "evenodd"

ARITHMETIC_TERMS: Final = 4

EXTRA_HINT: Final = "pip install 'svgwriter[graph]'"
GRAPH_SIZE: Final = 400.0
MARGIN: Final = 30.0
NODE_RADIUS: Final = 12.0
NODE_FILL: Final = "#4c9be8"
NODE_STROKE: Final = "#1e1e1e"
EDGE_STROKE: Final = "#555555"
EDGE_WIDTH: Final = 1.5
LABEL_SIZE: Final = 11.0
ARROW_LENGTH: Final = 9.0
ARROW_SPREAD: Final = 25.0
LAYOUTS: Final = ("spring", "kamada_kawai", "circular", "shell", "spectral", "planar", "random", "spiral")

HALF_TURN: Final = 180.0
FULL_TURN: Final = 360.0
DISCRETE_SWITCH: Final = 0.5
GEOMETRY_SKIP: Final = frozenset({"id", "transform", "d", "points"})

DEFAULT_STROKE_WIDTH: Final = 1.0
DEFAULT_MITER_LIMIT: Final = 4.0
MEASURE_PRECISION: Final = 16.0
CAPS: Final = {"butt": "kButt_Cap", "round": "kRound_Cap", "square": "kSquare_Cap"}
JOINS: Final = {"miter": "kMiter_Join", "round": "kRound_Join", "bevel": "kBevel_Join"}

SERIAL_LIMIT: Final = 2
CHANNEL_SCALE: Final = 255.0

MOVETO: Final = 1
LINETO: Final = 2
CURVE4: Final = 4
CLOSEPOLY: Final = 79
POINTS_PER_UNIT: Final = 0.75

DEFAULT_QUALITY: Final = 90
DISPLAY: Final = "display"
PIXEL_EPSILON: Final = 1e-6
FORMATS: Final = {"png": skia.kPNG, "jpeg": skia.kJPEG, "jpg": skia.kJPEG, "webp": skia.kWEBP}

DEFAULT_FAMILY: Final = "sans-serif"
NORMAL_WEIGHT: Final = 400
BOLD_WEIGHT: Final = 700
NORMAL_WIDTH: Final = 5
GENERIC_FAMILIES: Final = frozenset({"serif", "sans-serif", "monospace", "cursive", "fantasy"})
GENERIC_CANDIDATES: Final = {
    "serif": ("Times New Roman", "Georgia", "Times", "Liberation Serif", "DejaVu Serif", "Noto Serif"),
    "monospace": ("Consolas", "Courier New", "Menlo", "Monaco", "Liberation Mono", "DejaVu Sans Mono",
                  "Noto Sans Mono", "Courier"),
    "cursive": ("Comic Sans MS", "Segoe Script", "Apple Chancery", "URW Chancery L"),
    "fantasy": ("Impact", "Papyrus", "Luminari"),
}
ANCHOR_SHIFT: Final = {"start": 0.0, "middle": 0.5, "end": 1.0}
FONT_CACHE: Final = 64
GLYPH_CACHE: Final = 8192
COMPLEX_SCRIPT_START: Final = 0x0590
LATIN_EXTENDED_ADDITIONAL: Final = 0x1E00
CJK_START: Final = 0xA800
EMOJI_START: Final = 0x1F000
