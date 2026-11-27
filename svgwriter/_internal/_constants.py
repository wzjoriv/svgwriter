"""
Namespaces, defaults, unit conversion factors and shared tables.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "ID_ATTRIBUTE_RE",
    "TIMING_ATTRIBUTE_RE",
    "PAGE_LENGTH_DIGITS",
    "ANCHOR_SHIFT",
    "ANIMATED_DEFAULTS",
    "ATTRIBUTE_TABLE",
    "BASE_PROFILE",
    "BLINK_VALUES",
    "BOLD_WEIGHT",
    "BOUNCE_HEIGHT",
    "BOUNCE_TIMES",
    "BOUNCE_VALUES",
    "CHANNEL_MAX",
    "CJK_START",
    "CLOCK_RE",
    "CM_PER_INCH",
    "COLOR_ALIASES",
    "COLOR_GLYPH_TABLES",
    "COMPLEX_SCRIPT_START",
    "CONTAINERS",
    "CREATE_DRAW_SHARE",
    "DEFAULT_DURATION",
    "DEFAULT_FAMILY",
    "DEFAULT_FONT_SIZE",
    "DEFAULT_INDENT",
    "DEFAULT_MITER",
    "DEFAULT_MITER_LIMIT",
    "DEFAULT_PRECISION",
    "DEFAULT_SIZE",
    "DISPLAY_SCALE",
    "DOCTYPE",
    "DOT",
    "DROPPED_EFFECTS",
    "DVISVGM",
    "EASE_BEND_SAMPLES",
    "EASE_BISECTIONS",
    "EASE_CURVES",
    "EASE_GRID",
    "EASE_NEWTON_STEPS",
    "EASE_SAMPLES",
    "EMOJI_CELL_LEVELS",
    "EMOJI_END",
    "EMOJI_JOINERS",
    "EMOJI_MODIFIERS",
    "EMOJI_PIXELS_PER_EM",
    "EMOJI_PROBE",
    "EMOJI_START",
    "ENGINES",
    "EPSILON",
    "EX_PER_EM",
    "FEATURE_PREFIX",
    "FONT_CACHE",
    "FONT_SIZE_KEYWORDS",
    "FONT_WEIGHTS",
    "FOREVER",
    "FULL_TURN",
    "GENERIC_FAMILIES",
    "GHOST",
    "GLYPH_CACHE",
    "GRID",
    "GRID_STEP",
    "INDEFINITE",
    "INKSCAPE_LABEL",
    "INKSCAPE_NS",
    "JOIN_TOLERANCE",
    "KNOWN_NAMESPACES",
    "LATEX",
    "LATEX_SIZE",
    "LATEX_SOURCE",
    "LATEX_TEMPLATE",
    "LATIN_EXTENDED_ADDITIONAL",
    "LINK_CACHE",
    "SODIPODI_NS",
    "VIEWPORT_AXES",
    "TILE_OFFSETS",
    "TILE_COPY_SUFFIX",
    "USER_SPACE",
    "BASE64_SUFFIX",
    "GZIP_MAGIC",
    "SVG_DATA_URI",
    "DATA_URI",
    "VISIBILITY",
    "LINKED_OVERSAMPLE",
    "EXTERNAL_ID_PREFIX",
    "NESTED_VIEWPORT_ID",
    "LINEAR_RGB",
    "LINEAR_STOP_STEPS",
    "SRGB_GAMMA",
    "SRGB_LINEAR_SLOPE",
    "SRGB_OFFSET",
    "SRGB_THRESHOLD",
    "URL_REFERENCE_RE",
    "PRIMITIVE_PREFIX",
    "VIEWPORT_FALLBACK",
    "MARKER_DEFAULT_SIZE",
    "MARKER_PROPERTIES",
    "MARKER_SHORTHAND",
    "MOTION_HELPERS",
    "MARKER_CLIP_ID",
    "MARKABLE",
    "MARKER_FREE",
    "URL_OPEN",
    "COLOR_PROPERTIES",
    "COLOR_OPACITIES",
    "LEGACY_COLOR_RE",
    "CURRENT_COLOR",
    "INHERIT",
    "GRADIENT_TAGS",
    "PAINT_PROPERTIES",
    "SERVER_ATTRIBUTES",
    "XLINK_HREF",
    "OBJECT_BOUNDING_BOX",
    "SERVER_UNITS",
    "URL_PREFIX",
    "MATHTEXT_SIZE",
    "MAX_SEGMENTS",
    "MERMAID",
    "MM_PER_INCH",
    "MPL_CLOSE",
    "MPL_CURVE3",
    "MPL_CURVE4",
    "MPL_LINETO",
    "MPL_MOVETO",
    "NONE",
    "NON_CONTENT",
    "NORMAL_WEIGHT",
    "NORMAL_WIDTH",
    "NOT_RENDERED",
    "NUMBER_RE",
    "OUTLINE",
    "PC_PER_INCH",
    "PERCENT",
    "PT_PER_INCH",
    "PX_PER_INCH",
    "Q_PER_INCH",
    "PX_PER_PT",
    "PULSE_SCALE",
    "RENDER_LANGUAGE",
    "RGBA_CHANNELS",
    "RTL_ANCHORS",
    "SUGGESTIONS",
    "ENTRY_POINT_PREFIX",
    "SECONDS_PER_HOUR",
    "SECONDS_PER_MINUTE",
    "SHAKE_DISTANCE",
    "SHAKE_STEPS",
    "SIDES",
    "STROKE",
    "SVG_NS",
    "SYNCBASE_RE",
    "SYNC_DEPTH",
    "SVG_VERSION",
    "SWATCH",
    "TEXT_TABLE",
    "TEX_SIZE",
    "TIMECOUNT_RE",
    "TIMEOUT_SECONDS",
    "TIME_SCALE",
    "USE_GEOMETRY",
    "USE_NESTING",
    "VISIBLE_OVERFLOW",
    "WRITE_LAG",
    "XLINK_NS",
    "XML_NS",
    "ZIAMATH_SIZE",
]

SVG_NS: Final = "http://www.w3.org/2000/svg"
XLINK_NS: Final = "http://www.w3.org/1999/xlink"
XML_NS: Final = "http://www.w3.org/XML/1998/namespace"
INKSCAPE_NS: Final = "http://www.inkscape.org/namespaces/inkscape"
INKSCAPE_LABEL: Final = "inkscape:label"
SODIPODI_NS: Final = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
KNOWN_NAMESPACES: Final = {
    "xlink": XLINK_NS,
    "inkscape": INKSCAPE_NS,
    "sodipodi": SODIPODI_NS,
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "cc": "http://creativecommons.org/ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
}

SVG_VERSION: Final = "1.1"
BASE_PROFILE: Final = "full"
DOCTYPE: Final = (
    '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
    '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
)

DEFAULT_PRECISION: Final = 4
DEFAULT_INDENT: Final = "  "
INDEFINITE: Final = "indefinite"

PX_PER_INCH: Final = 96.0
DEFAULT_FONT_SIZE: Final = 16.0
EX_PER_EM: Final = 0.5
PT_PER_INCH: Final = 72.0
PX_PER_PT: Final = PX_PER_INCH / PT_PER_INCH
PC_PER_INCH: Final = 6.0
MM_PER_INCH: Final = 25.4
CM_PER_INCH: Final = 2.54
Q_PER_INCH: Final = MM_PER_INCH * 4

SWATCH: Final = 40.0
GRID: Final = 4
GRID_STEP: Final = 10.0
OUTLINE: Final = "#1e1e1e"
GHOST: Final = "#bbbbbb"
STROKE: Final = 1.0

TEXT_TABLE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;"})
ATTRIBUTE_TABLE = str.maketrans(
    {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "\n": "&#10;",
        "\r": "&#13;",
        "\t": "&#9;",
    }
)

NON_CONTENT: Final = frozenset({"defs", "style", "title", "desc", "metadata", "namedview"})

BOLD_WEIGHT: Final = 700
DEFAULT_FAMILY: Final = "sans-serif"
FONT_CACHE: Final = 64
GENERIC_FAMILIES: Final = frozenset({"serif", "sans-serif", "monospace", "cursive", "fantasy"})
GLYPH_CACHE: Final = 8192
NORMAL_WEIGHT: Final = 400
NORMAL_WIDTH: Final = 5
CJK_START: Final = 0xA800
COMPLEX_SCRIPT_START: Final = 0x0590
EMOJI_START: Final = 0x1F000
EMOJI_END: Final = 0x1FBFF
EMOJI_JOINERS: Final = frozenset({chr(0x200D), chr(0xFE0F), chr(0x20E3)})
EMOJI_MODIFIERS: Final = (0x1F3FB, 0x1F3FF)
EMOJI_PROBE: Final = "\U0001f600"
EMOJI_PIXELS_PER_EM: Final = 72
EMOJI_CELL_LEVELS: Final = 16
COLOR_GLYPH_TABLES: Final = ("COLR", "sbix", "CBDT", "SVG ")
LATIN_EXTENDED_ADDITIONAL: Final = 0x1E00
DEFAULT_MITER_LIMIT: Final = 4.0
ANCHOR_SHIFT: Final = {"start": 0.0, "middle": 0.5, "end": 1.0}
RTL_ANCHORS: Final = {"start": "end", "end": "start"}
CONTAINERS: Final = frozenset({"svg", "g", "a", "switch"})
NOT_RENDERED: Final = frozenset({"defs", "clipPath", "mask", "pattern", "marker", "symbol", "linearGradient",
                                 "radialGradient", "filter", "title", "desc", "metadata", "style", "font",
                                 "font-face", "glyph", "missing-glyph"})
LINK_CACHE: Final = 64
VIEWPORT_FALLBACK: Final = 300.0
SVG_DATA_URI: Final = "data:image/svg+xml"
DATA_URI: Final = "data:"
VISIBILITY: Final = "visibility"
LINKED_OVERSAMPLE: Final = 2.0
EXTERNAL_ID_PREFIX: Final = "svgwriter-external-"
NESTED_VIEWPORT_ID: Final = "svgwriter-svg-viewport-"
LINEAR_RGB: Final = "linearRGB"
LINEAR_STOP_STEPS: Final = 16
SRGB_GAMMA: Final = 2.4
SRGB_LINEAR_SLOPE: Final = 12.92
SRGB_OFFSET: Final = 0.055
SRGB_THRESHOLD: Final = 0.04045
URL_REFERENCE_RE: Final = re.compile(r"url\(\s*['\"]?#([^)'\"\s]+)")
PRIMITIVE_PREFIX: Final = "fe"
BASE64_SUFFIX: Final = ";base64"
GZIP_MAGIC: Final = b"\x1f\x8b"
VIEWPORT_AXES: Final = {"x": 0, "y": 1, "width": 0, "height": 1}
TILE_OFFSETS: Final = frozenset({"x", "y"})
TILE_COPY_SUFFIX: Final = "-svgwriter-tile-"
USER_SPACE: Final = "userSpaceOnUse"

CLOCK_RE: Final = re.compile(r"^\s*(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)\s*$")
EPSILON: Final = 1e-9
NUMBER_RE: Final = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
SECONDS_PER_HOUR: Final = 3600.0
SECONDS_PER_MINUTE: Final = 60.0
TIME_SCALE: Final = {"ms": 0.001, "s": 1.0, "min": 60.0, "h": 3600.0, None: 1.0}
TIMECOUNT_RE: Final = re.compile(r"^\s*([+-]?\d*\.?\d+)\s*(ms|s|min|h)?\s*$")

DEFAULT_MITER: Final = 4.0
NONE: Final = "none"
DROPPED_EFFECTS: Final = {"mask": ("mask",), "filter": ("filter",)}
MARKER_PROPERTIES: Final = ("marker-start", "marker-mid", "marker-end")
MARKER_DEFAULT_SIZE: Final = 3.0
MARKER_SHORTHAND: Final = "marker"
MARKER_CLIP_ID: Final = "svgwriter-marker-viewport-"
MARKABLE: Final = frozenset({"path", "line", "polyline", "polygon"})
MARKER_FREE: Final = frozenset({"marker", "defs", "clipPath", "mask", "pattern", "symbol"})
URL_OPEN: Final = "url(#"
CURRENT_COLOR: Final = "currentColor"
INHERIT: Final = "inherit"
XLINK_HREF: Final = "xlink:href"
GRADIENT_TAGS: Final = frozenset({"linearGradient", "radialGradient"})
PAINT_PROPERTIES: Final = ("fill", "stroke")
_GRADIENT_COMMON: Final = ("gradientUnits", "gradientTransform", "spreadMethod")
SERVER_ATTRIBUTES: Final = {
    "linearGradient": (*_GRADIENT_COMMON, "x1", "y1", "x2", "y2"),
    "radialGradient": (*_GRADIENT_COMMON, "cx", "cy", "r", "fx", "fy"),
    "pattern": ("patternUnits", "patternContentUnits", "patternTransform", "x", "y", "width", "height", "viewBox",
                "preserveAspectRatio"),
}
OBJECT_BOUNDING_BOX: Final = "objectBoundingBox"
URL_PREFIX: Final = "url("
SERVER_UNITS: Final = {"linearGradient": "gradientUnits", "radialGradient": "gradientUnits", "pattern": "patternUnits"}
COLOR_PROPERTIES: Final = frozenset({"fill", "stroke", "stop-color", "flood-color", "lighting-color"})
COLOR_OPACITIES: Final = {"fill": "fill-opacity", "stroke": "stroke-opacity", "stop-color": "stop-opacity",
                          "flood-color": "flood-opacity"}
"""The opacity property that carries the alpha of each colour property on a render copy."""
LEGACY_COLOR_RE: Final = re.compile(r"^(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|rgb\(\s*[\d.%]+\s*,\s*[\d.%]+\s*,\s*[\d.%]+\s*\)|[a-zA-Z]+)$")
"""Colour syntaxes every SVG 1.1 renderer reads: short and long hex, comma ``rgb()`` and keywords."""
PERCENT: Final = 100.0
DEFAULT_SIZE: Final = 16.0
JOIN_TOLERANCE: Final = 0.01

CHANNEL_MAX: Final = 255
RGBA_CHANNELS: Final = 4

COLOR_ALIASES: Final = {"masooma": "green"}

FONT_WEIGHTS: Final = {"normal": 400, "bold": 700, "bolder": 700, "lighter": 300}
FONT_SIZE_KEYWORDS: Final = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "medium": 16.0, "large": 18.0,
                             "x-large": 24.0, "xx-large": 32.0, "smaller": 13.0, "larger": 19.0}

BLINK_VALUES: Final = "1;0;1"
BOUNCE_HEIGHT: Final = 20.0
BOUNCE_TIMES: Final = (0.0, 0.25, 0.5, 0.65, 0.8, 0.9, 1.0)
BOUNCE_VALUES: Final = (0.0, 1.0, 0.0, 0.45, 0.0, 0.15, 0.0)
CREATE_DRAW_SHARE: Final = 0.6
DEFAULT_DURATION: Final = 1.0
FOREVER: Final = "indefinite"
PULSE_SCALE: Final = 1.1
SHAKE_DISTANCE: Final = 4.0
SHAKE_STEPS: Final = 6
WRITE_LAG: Final = 0.35
SIDES: Final = {"left": (-1.0, 0.0), "right": (1.0, 0.0), "top": (0.0, -1.0), "bottom": (0.0, 1.0)}

FULL_TURN: Final = 360.0

EASE_CURVES: Final = {"linear": (0.0, 0.0, 1.0, 1.0), "ease": (0.25, 0.1, 0.25, 1.0),
                      "ease-in": (0.42, 0.0, 1.0, 1.0), "ease-out": (0.0, 0.0, 0.58, 1.0),
                      "ease-in-out": (0.42, 0.0, 0.58, 1.0)}
EASE_NEWTON_STEPS: Final = 8
EASE_BISECTIONS: Final = 48
EASE_GRID: Final = 256
EASE_SAMPLES: Final = (24, 60)
EASE_BEND_SAMPLES: Final = 6.0

MAX_SEGMENTS: Final = 512

DOT: Final = "dot"
MERMAID: Final = "mmdc"
LATEX: Final = "latex"
DVISVGM: Final = "dvisvgm"
TIMEOUT_SECONDS: Final = 60
ENGINES: Final = ("auto", "tex", "ziamath", "mathtext")
LATEX_TEMPLATE: Final = (r"\documentclass[preview,border=0pt]{{standalone}}" "\n"
                         r"\usepackage{{amsmath,amssymb}}" "\n"
                         r"\begin{{document}}" "\n{body}\n" r"\end{{document}}" "\n")
ZIAMATH_SIZE: Final = 10.0
TEX_SIZE: Final = 10.0
LATEX_SOURCE: Final = "data-latex"
LATEX_SIZE: Final = "data-latex-size"
MATHTEXT_SIZE: Final = 10.0
DISPLAY_SCALE: Final = 1.2
MPL_MOVETO: Final = 1
MPL_LINETO: Final = 2
MPL_CURVE3: Final = 3
MPL_CURVE4: Final = 4
MPL_CLOSE: Final = 79
USE_GEOMETRY: Final = frozenset({"x", "y", "width", "height", "xlink:href", "href", "transform", "id"})
USE_NESTING: Final = 16
VISIBLE_OVERFLOW: Final = frozenset({"visible", "auto"})
SYNCBASE_RE: Final = re.compile(r"^\s*([^\s.;+-][^;]*?)\.(begin|end)\s*(?:([+-])\s*(\S.*?))?\s*$")
SYNC_DEPTH: Final = 32
ANIMATED_DEFAULTS: Final = {
    "fill": "black", "stroke": "none", "color": "black", "opacity": "1", "fill-opacity": "1", "stroke-opacity": "1",
    "stroke-width": "1", "stop-color": "black", "stop-opacity": "1", "flood-color": "black", "flood-opacity": "1",
    "lighting-color": "white", "x": "0", "y": "0", "cx": "0", "cy": "0", "dx": "0", "dy": "0", "x1": "0",
    "y1": "0", "x2": "0", "y2": "0", "stroke-dashoffset": "0", "font-size": "16",
}
RENDER_LANGUAGE: Final = "en"
FEATURE_PREFIX: Final = "http://www.w3.org/TR/SVG11/feature#"
SUGGESTIONS: Final = 3
ENTRY_POINT_PREFIX: Final = "svgwriter."
MOTION_HELPERS: Final = frozenset({"apply", "stagger", "element"})

PAGE_LENGTH_DIGITS: Final = 9
"""Decimal places kept when a length converts to user units of a physically sized page."""

ID_ATTRIBUTE_RE: Final = re.compile(r'(?<![\w-])id="([^"]+)"')
"""An ``id`` attribute in serialized markup; group 1 is the id."""
TIMING_ATTRIBUTE_RE: Final = re.compile(r'(?<![\w-])(begin|end)="([^"]*)"')
"""A SMIL ``begin`` or ``end`` attribute; group 2 is its value (may name other elements' ids)."""
