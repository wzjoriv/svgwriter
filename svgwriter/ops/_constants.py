"""
Constants for ``svgwriter.ops``: defaults, tables and patterns.
"""

from __future__ import annotations

import re
from typing import Final

import skia

__all__ = [
    "STAMP_STYLES",
    "WIREFRAME_BOUNDS_DASH",
    "WIREFRAME_COLOR",
    "WIREFRAME_DROPPED",
    "WIREFRAME_WIDTH",
    "WIREFRAME_WIDTH_SHARE",
    "ALPHA_ONLY",
    "ARC_HANDLE",
    "ARITHMETIC_TERMS",
    "ARROW_LENGTH",
    "ARROW_SPREAD",
    "BLEND",
    "CAPS",
    "CHANNEL_MAX",
    "CHANNEL_SCALE",
    "CLOSEPOLY",
    "COMPOSITE",
    "CONIC_SUBDIVISION",
    "CURVE4",
    "DEFAULT_FAMILY",
    "FAMILY_IDENTIFIER",
    "DEFAULT_FONT_SIZE",
    "DEFAULT_QUALITY",
    "DEFAULT_STROKE_WIDTH",
    "DISCRETE_SWITCH",
    "DISPLAY",
    "EDGE_STROKE",
    "EDGE_WIDTH",
    "EFFECTS",
    "EVENODD",
    "FORMATS",
    "FULL_TURN",
    "GEOMETRY_SKIP",
    "GLYPH_CACHE",
    "GRAPH_LAYOUTS",
    "GRAPH_SIZE",
    "GRAPH_TYPES",
    "IGRAPH_LAYOUT_NAMES",
    "HALF_TURN",
    "JOINS",
    "LABEL_BASELINE",
    "LABEL_SIZE",
    "LINETO",
    "LUMA",
    "MARGIN",
    "MUTUAL_BEND",
    "MASK_CANVAS",
    "MEASURE_PRECISION",
    "MISSING_GLYPH",
    "MORPH_CORNER",
    "MORPH_FLATNESS",
    "MORPH_MAX_POINTS",
    "MORPH_MIN_POINTS",
    "MORPH_SPACING",
    "MOVETO",
    "CORNER_TOLERANCE",
    "LENGTH_SEARCH_STEPS",
    "NODE_FILL",
    "OPEN_BOOLEAN_WARNING",
    "NODE_RADIUS",
    "NODE_STROKE",
    "NO_DECORATION",
    "PIXEL_EPSILON",
    "POINTS_PER_UNIT",
    "POSITION_TOLERANCE",
    "SEARCHABLE_ALPHA",
    "SERIAL_LIMIT",
    "SOURCE_ALPHA",
    "FILTER_REGION_DEFAULT",
    "ENGINE_PRIMITIVES",
    "CHANNELS",
    "LINEAR_RGB",
    "COLOR_MIXING",
    "FRAMED",
    "CONVOLVE_ORDER",
    "EDGE_MODES",
    "PICTURE_BOUNDS",
    "SOURCE_GRAPHIC",
    "LIGHT_SOURCES",
    "SPOT_CUTOFF",
    "LIGHTING",
    "CONCEALED",
    "BACKGROUND_IMAGE",
    "BACKGROUND_ALPHA",
    "FILL_PAINT",
    "STROKE_PAINT",
    "PAINT_INPUTS",
    "STANDARD_INPUTS",
    "ENABLE_BACKGROUND",
    "NEW_BACKGROUND",
    "OPACITY",
    "DISPLACEMENT",
    "COVERAGE_WHITE",
    "SEEDED_LAYOUTS",
]

SOURCE_GRAPHIC: Final = "SourceGraphic"
SOURCE_ALPHA: Final = "SourceAlpha"
BACKGROUND_IMAGE: Final = "BackgroundImage"
BACKGROUND_ALPHA: Final = "BackgroundAlpha"
FILL_PAINT: Final = "FillPaint"
STROKE_PAINT: Final = "StrokePaint"
PAINT_INPUTS: Final = frozenset({FILL_PAINT, STROKE_PAINT})
STANDARD_INPUTS: Final = frozenset({BACKGROUND_IMAGE, BACKGROUND_ALPHA, FILL_PAINT, STROKE_PAINT})
ENABLE_BACKGROUND: Final = "enable-background"
NEW_BACKGROUND: Final = "new"
ALPHA_ONLY: Final = [0.0] * 15 + [0.0, 0.0, 0.0, 1.0, 0.0]
COVERAGE_WHITE: Final = [0.0, 0.0, 0.0, 0.0, 1.0] * 3 + [0.0, 0.0, 0.0, 1.0, 0.0]
LUMA: Final = (0.2125, 0.7154, 0.0721)
BLEND: Final = {"normal": skia.BlendMode.kSrcOver, "multiply": skia.BlendMode.kMultiply,
                "screen": skia.BlendMode.kScreen, "darken": skia.BlendMode.kDarken,
                "lighten": skia.BlendMode.kLighten}
COMPOSITE: Final = {"over": skia.BlendMode.kSrcOver, "in": skia.BlendMode.kSrcIn, "out": skia.BlendMode.kSrcOut,
                    "atop": skia.BlendMode.kSrcATop, "xor": skia.BlendMode.kXor}
MASK_CANVAS: Final = 1e6
PICTURE_BOUNDS: Final = 1e6
FILTER_REGION_DEFAULT: Final = (-0.1, 1.2)
ENGINE_PRIMITIVES: Final = frozenset({"feImage", "feTile", "feConvolveMatrix", "feDiffuseLighting", "feSpecularLighting"})
CHANNELS: Final = {"R": skia.ColorChannel.kR, "G": skia.ColorChannel.kG, "B": skia.ColorChannel.kB,
                   "A": skia.ColorChannel.kA}
LINEAR_RGB: Final = "linearRGB"
CONVOLVE_ORDER: Final = 3
EDGE_MODES: Final = {"duplicate": skia.TileMode.kClamp, "wrap": skia.TileMode.kRepeat, "none": skia.TileMode.kDecal}
LIGHT_SOURCES: Final = frozenset({"feDistantLight", "fePointLight", "feSpotLight"})
LIGHTING: Final = frozenset({"feDiffuseLighting", "feSpecularLighting"})
SPOT_CUTOFF: Final = 90.0
DISPLACEMENT: Final = "feDisplacementMap"
FRAMED: Final = frozenset({"feImage", "feTile", DISPLACEMENT})
COLOR_MIXING: Final = frozenset({"feBlend", "feComposite", "feMerge", "feGaussianBlur", "feColorMatrix",
                                 "feComponentTransfer", "feMorphology", "feConvolveMatrix",
                                 "feDiffuseLighting", "feSpecularLighting"})

CHANNEL_MAX: Final = 255

EFFECTS: Final = ("filter", "mask")
NO_DECORATION: Final = ("", "none")
DEFAULT_FONT_SIZE: Final = 16.0
SEARCHABLE_ALPHA: Final = 1 / 255
MISSING_GLYPH: Final = 0
POSITION_TOLERANCE: Final = 0.01

CONIC_SUBDIVISION: Final = 3
EVENODD: Final = "evenodd"

ARITHMETIC_TERMS: Final = 4

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
GRAPH_LAYOUTS: Final = {
    "networkx": ("spring", "kamada_kawai", "circular", "shell", "spectral", "planar", "random", "spiral"),
    "igraph": ("spring", "circular", "kamada_kawai", "fruchterman_reingold", "drl", "graphopt", "grid", "random",
               "reingold_tilford", "reingold_tilford_circular", "star", "sugiyama", "mds", "lgl", "davidson_harel"),
    "rustworkx": ("spring", "kamada_kawai", "circular", "shell", "spiral", "random"),
}
GRAPH_TYPES: Final = {"networkx": ("adj", "nodes"), "igraph": ("vs", "es"), "rustworkx": ("node_indices", "weighted_edge_list")}
IGRAPH_LAYOUT_NAMES: Final = {"spring": "fruchterman_reingold", "circular": "circle"}
SEEDED_LAYOUTS: Final = ("spring", "random")
LABEL_BASELINE: Final = 0.35
MUTUAL_BEND: Final = 0.15

HALF_TURN: Final = 180.0
FULL_TURN: Final = 360.0
DISCRETE_SWITCH: Final = 0.5
GEOMETRY_SKIP: Final = frozenset({"id", "transform", "d", "points"})
MORPH_SPACING: Final = 0.012
MORPH_FLATNESS: Final = 0.001
MORPH_MIN_POINTS: Final = 24
MORPH_MAX_POINTS: Final = 600
MORPH_CORNER: Final = 0.35

DEFAULT_STROKE_WIDTH: Final = 1.0
MEASURE_PRECISION: Final = 16.0
CORNER_TOLERANCE: Final = 0.01
ARC_HANDLE: Final = 4 / 3
LENGTH_SEARCH_STEPS: Final = 48
OPEN_BOOLEAN_WARNING: Final = (
    "the {name} is empty: boolean operations combine filled areas, and an open path (no Z) "
    "such as a line encloses none; close it with Z, or call .stroked() to turn the line into an area"
)
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
OPACITY: Final = "opacity"
CONCEALED: Final = (DISPLAY, "filter")
PIXEL_EPSILON: Final = 1e-6
FORMATS: Final = {"png": skia.kPNG, "jpeg": skia.kJPEG, "jpg": skia.kJPEG, "webp": skia.kWEBP}

DEFAULT_FAMILY: Final = "sans-serif"
GLYPH_CACHE: Final = 8192
FAMILY_IDENTIFIER: Final = re.compile(r"[A-Za-z_][\w-]*(?: [A-Za-z_][\w-]*)*")

WIREFRAME_COLOR: Final = "#0ea5e9"
"""Outline colour of a wireframe."""
WIREFRAME_WIDTH: Final = 1.0
"""Outline width of a wireframe whose size is unknown, in user units."""
WIREFRAME_WIDTH_SHARE: Final = 600
"""A wireframe's default outline is the drawing's larger side divided by this."""
WIREFRAME_BOUNDS_DASH: Final = "4 3"
"""Dash pattern of the bounding boxes a wireframe can draw."""
WIREFRAME_DROPPED: Final = ("filter", "mask", "clip-path", "opacity", "fill-opacity", "stroke-opacity", "marker-start",
                            "marker-mid", "marker-end", "stroke-dasharray")
"""Attributes and style properties a wireframe leaves out, so only the geometry shows."""
STAMP_STYLES: Final = {"rotate": "kRotate_Style", "translate": "kTranslate_Style", "morph": "kMorph_Style"}
"""How a stamped shape follows its path, and the skia style for each."""
