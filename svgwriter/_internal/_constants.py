"""
Namespaces, defaults, unit conversion factors and shared tables.
"""

from __future__ import annotations

import re
from typing import Final

import numpy as np

__all__ = [
    "ANCHOR_SHIFT",
    "ANIMATED_DEFAULTS",
    "ATTRIBUTE_TABLE",
    "BASE_PROFILE",
    "BLINK_VALUES",
    "BMP_BITS_PER_PIXEL",
    "BMP_BI_BITFIELDS",
    "BMP_FILE_HEADER_SIZE",
    "BMP_LCS_SRGB",
    "BMP_MAGIC",
    "BMP_MASKS",
    "BMP_PIXELS_PER_METER",
    "BMP_V4_HEADER_SIZE",
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
    "DEFAULT_DPI",
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
    "FONT_CACHE",
    "FONT_SIZE_KEYWORDS",
    "FONT_WEIGHTS",
    "FOREVER",
    "FULL_TURN",
    "GENERIC_CANDIDATES",
    "GENERIC_FAMILIES",
    "GHOST",
    "GIF_APPLICATION",
    "GIF_APPLICATION_SIZE",
    "GIF_BLOCK_SIZE",
    "GIF_CENTISECONDS",
    "GIF_DISPOSE_BACKGROUND",
    "GIF_EXTENSION",
    "GIF_FLAG_TRANSPARENT",
    "GIF_GRAPHIC_CONTROL",
    "GIF_GRAPHIC_CONTROL_SIZE",
    "GIF_HEADER",
    "GIF_IMAGE_SEPARATOR",
    "GIF_LOOP_BLOCK_SIZE",
    "GIF_MAX_CODES",
    "GIF_MAX_CODE_SIZE",
    "GIF_MAX_COLORS",
    "GIF_MAX_DIMENSION",
    "GIF_MIN_CODE_SIZE",
    "GIF_MIN_PALETTE",
    "GIF_NETSCAPE",
    "GIF_OPAQUE_THRESHOLD",
    "GIF_PALETTE_FLAG",
    "GIF_TRAILER",
    "GLYPH_CACHE",
    "GRID",
    "GRID_STEP",
    "INDEFINITE",
    "INSTALL_HINT",
    "JOIN_TOLERANCE",
    "LATEX",
    "LATEX_SIZE",
    "LATEX_SOURCE",
    "LATEX_TEMPLATE",
    "LATIN_EXTENDED_ADDITIONAL",
    "LINK_CACHE",
    "LUMA",
    "MAC_FALLBACK_FAMILIES",
    "MARKER_DEFAULT_SIZE",
    "MARKER_PROPERTIES",
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
    "PNM_BINARY_FROM",
    "PNM_BITMAP",
    "PNM_COMMENT",
    "PNM_MAGIC",
    "PNM_WHITESPACE",
    "PT_PER_INCH",
    "PULSE_SCALE",
    "RGBA_CHANNELS",
    "RTL_ANCHORS",
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
    "UINT16_MAX",
    "USE_GEOMETRY",
    "USE_NESTING",
    "VISIBLE_OVERFLOW",
    "WHITE",
    "WRITE_LAG",
    "XLINK_NS",
    "XML_NS",
    "ZIAMATH_SIZE",
]

SVG_NS: Final = "http://www.w3.org/2000/svg"
XLINK_NS: Final = "http://www.w3.org/1999/xlink"
XML_NS: Final = "http://www.w3.org/XML/1998/namespace"

SVG_VERSION: Final = "1.1"
BASE_PROFILE: Final = "full"
DOCTYPE: Final = (
    '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
    '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
)

DEFAULT_PRECISION: Final = 4
DEFAULT_INDENT: Final = "  "
INDEFINITE: Final = "indefinite"

DEFAULT_DPI: Final = 96.0
DEFAULT_FONT_SIZE: Final = 16.0
EX_PER_EM: Final = 0.5
PT_PER_INCH: Final = 72.0
PC_PER_INCH: Final = 6.0
MM_PER_INCH: Final = 25.4
CM_PER_INCH: Final = 2.54

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

NON_CONTENT: Final = frozenset({"defs", "style", "title", "desc", "metadata"})

BOLD_WEIGHT: Final = 700
DEFAULT_FAMILY: Final = "sans-serif"
FONT_CACHE: Final = 64
GENERIC_CANDIDATES: Final = {
    "sans-serif": ("Arial", "Helvetica", "Liberation Sans", "Arimo", "DejaVu Sans", "Noto Sans"),
    "serif": ("Times New Roman", "Georgia", "Times", "Liberation Serif", "DejaVu Serif", "Noto Serif"),
    "monospace": ("Consolas", "Courier New", "Menlo", "Monaco", "Liberation Mono", "DejaVu Sans Mono",
                  "Noto Sans Mono", "Courier"),
    "cursive": ("Comic Sans MS", "Segoe Script", "Apple Chancery", "URW Chancery L"),
    "fantasy": ("Impact", "Papyrus", "Luminari"),
}
GENERIC_FAMILIES: Final = frozenset({"serif", "sans-serif", "monospace", "cursive", "fantasy"})
GLYPH_CACHE: Final = 8192
MAC_FALLBACK_FAMILIES: Final = (
    "Helvetica Neue", "Arial Unicode MS", "PingFang SC", "Hiragino Sans", "Apple SD Gothic Neo",
    "Kohinoor Devanagari", "Kohinoor Bangla", "Geeza Pro", "Noto Nastaliq Urdu", "Thonburi", "Apple Color Emoji",
)
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
PERCENT: Final = 100.0
DEFAULT_SIZE: Final = 16.0
JOIN_TOLERANCE: Final = 0.01

CHANNEL_MAX: Final = 255
RGBA_CHANNELS: Final = 4
LUMA: Final = np.array([0.299, 0.587, 0.114], np.float64)
PNM_BINARY_FROM: Final = 4
PNM_BITMAP: Final = (1, 4)
PNM_COMMENT: Final = re.compile(rb"#[^\r\n]*")
PNM_MAGIC: Final = re.compile(rb"P[1-6]")
PNM_WHITESPACE: Final = b" \t\r\n\v\f"
UINT16_MAX: Final = 65535
WHITE: Final = (255, 255, 255)
GIF_APPLICATION: Final = 0xFF
GIF_APPLICATION_SIZE: Final = 11
GIF_BLOCK_SIZE: Final = 255
GIF_CENTISECONDS: Final = 100
GIF_DISPOSE_BACKGROUND: Final = 0x08
GIF_EXTENSION: Final = 0x21
GIF_FLAG_TRANSPARENT: Final = 0x01
GIF_GRAPHIC_CONTROL: Final = 0xF9
GIF_GRAPHIC_CONTROL_SIZE: Final = 4
GIF_HEADER: Final = b"GIF89a"
GIF_IMAGE_SEPARATOR: Final = 0x2C
GIF_LOOP_BLOCK_SIZE: Final = 3
GIF_MAX_CODE_SIZE: Final = 12
GIF_MAX_CODES: Final = 1 << GIF_MAX_CODE_SIZE
GIF_MAX_COLORS: Final = 256
GIF_MAX_DIMENSION: Final = UINT16_MAX
GIF_MIN_CODE_SIZE: Final = 2
GIF_MIN_PALETTE: Final = 2
GIF_NETSCAPE: Final = b"NETSCAPE2.0"
GIF_OPAQUE_THRESHOLD: Final = 128
GIF_PALETTE_FLAG: Final = 0x80
GIF_TRAILER: Final = b"\x3b"
BMP_BI_BITFIELDS: Final = 3
BMP_BITS_PER_PIXEL: Final = 32
BMP_FILE_HEADER_SIZE: Final = 14
BMP_LCS_SRGB: Final = 0x73524742
BMP_MAGIC: Final = b"BM"
BMP_MASKS: Final = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
BMP_PIXELS_PER_METER: Final = 2835
BMP_V4_HEADER_SIZE: Final = 108

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
INSTALL_HINT: Final = {
    DOT: "install Graphviz (https://graphviz.org/download/) so that `dot` is on PATH",
    MERMAID: "install the Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`) so that `mmdc` is on PATH",
    LATEX: "install a TeX distribution (TeX Live or MiKTeX) so that `latex` is on PATH",
    DVISVGM: "install dvisvgm (bundled with TeX Live and MiKTeX) so that `dvisvgm` is on PATH",
    "plantuml": "install PlantUML so that `plantuml` is on PATH",
    "d2": "install D2 (https://d2lang.com) so that `d2` is on PATH",
}
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
