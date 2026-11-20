"""
Constants for the PDF, EPS and TikZ exporters and readers.
"""

from __future__ import annotations

import math
import re
import struct
from typing import Final

__all__ = [
    "ANCHORS",
    "ANGLE_EPSILON",
    "AXIAL",
    "BASE_LEVEL",
    "BEZIER_ARC_FACTOR",
    "BF_CHAR_RE",
    "BF_RANGE_RE",
    "BLACK",
    "BOUNDS_RE",
    "BRACKETS",
    "CAP_NAMES",
    "CHANNEL_MAX",
    "CLIP_TOLERANCE",
    "CMYK_CHANNELS",
    "COLORLET_RE",
    "COMMAND_PAINTS",
    "COMMENT_RE",
    "COMPONENTS",
    "DASHES",
    "DASH_RE",
    "DEFAULT_FONT",
    "DEFAULT_LINE_WIDTH",
    "DEFAULT_MEDIABOX",
    "DEFAULT_MITER",
    "DEFAULT_TEXT_SIZE",
    "DEFAULT_UNIT",
    "DEFINECOLOR_RE",
    "DELIMITERS",
    "DIAGONAL",
    "DIMENSION_RE",
    "DOS_EPS_HEADER",
    "DOS_EPS_MAGIC",
    "ENCRYPT_RE",
    "ENDSTREAM_RE",
    "EPS_CAPS",
    "EPS_CHANNEL_MAX",
    "EPS_JOINS",
    "EPS_PRECISION",
    "ESCAPE_RE",
    "EVENT_RE",
    "EXPONENTIAL",
    "FLATE",
    "FOREACH_RE",
    "FULL_TURN",
    "GAP_TOLERANCE",
    "GRAY_CHANNELS",
    "HAIRLINE",
    "HEADER_WINDOW",
    "HEX_DIGITS_RE",
    "HEX_END",
    "HEX_LINE",
    "HEX_RE",
    "IDENTITY_MATRIX",
    "IMAGE_OPERATORS",
    "INLINE_IMAGE_END_RE",
    "INLINE_LOOKBACK",
    "INNER_SEP",
    "JOIN_NAMES",
    "LATEX_SPECIALS",
    "LEVEL_LINE",
    "LINE_SPREAD",
    "LINE_WIDTHS",
    "LITERALS",
    "MACRO_RE",
    "MARKUP_RE",
    "MASK_THRESHOLD",
    "MATRIX_TOLERANCE",
    "MAX_ARC_SEGMENT",
    "MAX_IMAGE_CALLS",
    "MAX_LOOPS",
    "MAX_LOOP_ITEMS",
    "MAX_STEPS",
    "MAX_STYLE_DEPTH",
    "MONOSPACE_WORDS",
    "NAME_ESCAPE_RE",
    "NODE_BASELINE",
    "NODE_COMMANDS",
    "NODE_FONT_SIZE",
    "NODE_POSITIONS",
    "NODE_SHAPES",
    "NODE_TEXT_HEIGHT",
    "OBJECT_RE",
    "PAINTS",
    "PATH_TOKEN_RE",
    "PDF_HEADER",
    "PDF_MAX_DEPTH",
    "PDF_TOKEN_RE",
    "PERCENT",
    "PICTURE_RE",
    "POSITIONS",
    "POSTSCRIPT_FONTS",
    "PS_ESCAPES",
    "PS_HEADER",
    "PS_MAX_DEPTH",
    "PS_TOKEN_RE",
    "RADIAL",
    "RANGE_RE",
    "REGULAR",
    "RGB_CHANNELS",
    "RGB_SCALE",
    "SAVE_OBJECT",
    "SERIF_WORDS",
    "SHADING",
    "SHADING_LEVEL",
    "SIMPLE_ESCAPES",
    "SPACE_RE",
    "STITCHING",
    "STREAM_RE",
    "STYLE_RE",
    "SUBSET_RE",
    "SUPPORTED_BITS",
    "TEX_PT_PER_INCH",
    "TIKZSET_RE",
    "TIKZSTYLE_RE",
    "TIKZ_CAPS",
    "TIKZ_CAP_NAMES",
    "TIKZ_EMOJI_PIXELS",
    "TIKZ_JOINS",
    "TIKZ_PRECISION",
    "TILING",
    "UNITS",
    "WORD_RE",
    "XCOLOR",
]

EPS_PRECISION: Final = 3
EPS_CAPS: Final = {"butt": 0, "round": 1, "square": 2}
EPS_JOINS: Final = {"miter": 0, "round": 1, "bevel": 2}
BASE_LEVEL: Final = 2
LEVEL_LINE: Final = 4
EPS_CHANNEL_MAX: Final = 255
HEX_LINE: Final = 120
SHADING_LEVEL: Final = 3
MASK_THRESHOLD: Final = 0.5
TIKZ_EMOJI_PIXELS: Final = 24
AXIAL: Final = 2
RADIAL: Final = 3
POSTSCRIPT_FONTS: Final = {
    ("sans", False, False): "Helvetica", ("sans", True, False): "Helvetica-Bold",
    ("sans", False, True): "Helvetica-Oblique", ("sans", True, True): "Helvetica-BoldOblique",
    ("serif", False, False): "Times-Roman", ("serif", True, False): "Times-Bold",
    ("serif", False, True): "Times-Italic", ("serif", True, True): "Times-BoldItalic",
    ("mono", False, False): "Courier", ("mono", True, False): "Courier-Bold",
    ("mono", False, True): "Courier-Oblique", ("mono", True, True): "Courier-BoldOblique",
}
MONOSPACE_WORDS: Final = ("mono", "courier", "consolas", "menlo")
SERIF_WORDS: Final = ("times", "georgia", "garamond")
PS_ESCAPES: Final = {"\\": "\\\\", "(": "\\(", ")": "\\)"}
PS_HEADER: Final = b"%!"
DOS_EPS_MAGIC: Final = b"\xc5\xd0\xd3\xc6"
DOS_EPS_HEADER: Final = struct.Struct("<4sII")
PS_MAX_DEPTH: Final = 64
MAX_STEPS: Final = 2_000_000
SAVE_OBJECT: Final = object()
CAP_NAMES: Final = ("butt", "round", "square")
JOIN_NAMES: Final = ("miter", "round", "bevel")
CHANNEL_MAX: Final = 255.0
GRAY_CHANNELS: Final = 1
RGB_CHANNELS: Final = 3
CMYK_CHANNELS: Final = 4
SUPPORTED_BITS: Final = 8
MAX_IMAGE_CALLS: Final = 100_000
IMAGE_OPERATORS: Final = (b"image", b"colorimage")
INLINE_LOOKBACK: Final = 8
HEX_END: Final = b">"
DEFAULT_FONT: Final = "serif"
HEX_DIGITS_RE: Final = re.compile(rb"[^0-9A-Fa-f]")
ESCAPE_RE: Final = re.compile(rb"\\([0-7]{1,3}|\r\n|\n|\r|.)", re.S)
SIMPLE_ESCAPES: Final = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}
DELIMITERS: Final = rb"\x00\t\n\x0c\r ()<>\[\]{}/%"
PS_TOKEN_RE: Final = re.compile(
    rb"(?P<skip>[\x00\t\n\x0c\r ]+|%[^\r\n]*)"
    rb"|(?P<radix>\d+#[0-9A-Za-z]+)(?![^" + DELIMITERS + rb"])"
    rb"|(?P<num>[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)(?![^" + DELIMITERS + rb"])"
    rb"|(?P<literal>/[^" + DELIMITERS + rb"]*)"
    rb"|(?P<string>\()"
    rb"|(?P<a85><~.*?~>)"
    rb"|(?P<dict><<|>>)"
    rb"|(?P<hex><[^<>]*>)"
    rb"|(?P<open>\{)|(?P<close>\})"
    rb"|(?P<name>[\[\]]|[^" + DELIMITERS + rb"]+)"
    rb"|(?P<other>.)", re.S)
BOUNDS_RE: Final = {name: re.compile(rb"^%%" + name + rb":\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)",
                                      re.M) for name in (b"HiResBoundingBox", b"BoundingBox")}
COMPONENTS: Final = {"DeviceRGB": 3, "DeviceGray": 1, "DeviceCMYK": 4, "CalRGB": 3, "CalGray": 1}
DEFAULT_TEXT_SIZE: Final = 12.0
MATRIX_TOLERANCE: Final = 1e-4
GAP_TOLERANCE: Final = 0.05
SUBSET_RE: Final = re.compile(r"^[A-Z]{6}\+")
STYLE_RE: Final = re.compile(r"[-,]?(Bold|Italic|Oblique|BoldItalic|Regular|Roman|MT|PS)+$", re.I)
WORD_RE: Final = re.compile(r"(?<=[a-z])(?=[A-Z])")
HEX_RE: Final = re.compile(r"<([0-9A-Fa-f]+)>")
BF_CHAR_RE: Final = re.compile(r"beginbfchar(.*?)endbfchar", re.S)
BF_RANGE_RE: Final = re.compile(r"beginbfrange(.*?)endbfrange", re.S)
RANGE_RE: Final = re.compile(r"<([0-9A-Fa-f]+)>" + r"\s*<([0-9A-Fa-f]+)>" + r"\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])")
TILING: Final = 1
SHADING: Final = 2
EXPONENTIAL: Final = 2
STITCHING: Final = 3
IDENTITY_MATRIX: Final = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
PDF_HEADER: Final = b"%PDF-"
HEADER_WINDOW: Final = 1024
DEFAULT_MEDIABOX: Final = (0.0, 0.0, 612.0, 792.0)
PDF_MAX_DEPTH: Final = 32
FLATE: Final = ("FlateDecode", "Fl")
REGULAR: Final = rb"[^\x00\t\n\x0c\r ()<>\[\]{}/%]"
PDF_TOKEN_RE: Final = re.compile(
    rb"(?P<skip>[\x00\t\n\x0c\r ]+|%[^\r\n]*)"
    rb"|(?P<num>[+-]?(?:\d+\.?\d*|\.\d+))(?!" + REGULAR + rb")"
    rb"|(?P<name>/" + REGULAR + rb"*)"
    rb"|(?P<dict><<|>>)"
    rb"|(?P<hex><[^<>]*>)"
    rb"|(?P<string>\()"
    rb"|(?P<word>" + REGULAR + rb"+|[\[\]{}])"
    rb"|(?P<other>.)", re.S)
OBJECT_RE: Final = re.compile(rb"(?<!\d)(\d+)\s+(\d+)\s+obj(?!" + REGULAR + rb")")
STREAM_RE: Final = re.compile(rb"\s*stream(?:\r\n|\n|\r)")
ENDSTREAM_RE: Final = re.compile(rb"\s*endstream")
INLINE_IMAGE_END_RE: Final = re.compile(rb"\sEI(?=\s|$)")
ENCRYPT_RE: Final = re.compile(rb"/Encrypt\s*(?:\d+\s+\d+\s+R|<<)")
NAME_ESCAPE_RE: Final = re.compile(rb"#([0-9A-Fa-f]{2})")
LITERALS: Final = {b"true": True, b"false": False, b"null": None}
# fill, stroke, even-odd, close first
PAINTS: Final = {
    "S": (False, True, False, False), "s": (False, True, False, True),
    "f": (True, False, False, False), "F": (True, False, False, False), "f*": (True, False, True, False),
    "B": (True, True, False, False), "B*": (True, True, True, False),
    "b": (True, True, False, True), "b*": (True, True, True, True),
}
BLACK: Final = (0.0, 0.0, 0.0)
DEFAULT_MITER: Final = 4.0
HAIRLINE: Final = 0.25
MAX_ARC_SEGMENT: Final = math.pi / 2
BEZIER_ARC_FACTOR: Final = 4.0 / 3.0
TIKZ_PRECISION: Final = 3
ANGLE_EPSILON: Final = 1e-6
TIKZ_CAPS: Final = {"butt": "butt", "round": "round", "square": "rect"}
TIKZ_JOINS: Final = {"miter": "miter", "round": "round", "bevel": "bevel"}
LATEX_SPECIALS: Final = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "#": r"\#", "$": r"\$", "%": r"\%", "&": r"\&",
    "_": r"\_", "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
}
LINE_SPREAD: Final = 1.2
TEX_PT_PER_INCH: Final = 72.27
UNITS: Final = {"pt": 1.0, "bp": TEX_PT_PER_INCH / 72.0, "in": TEX_PT_PER_INCH, "cm": TEX_PT_PER_INCH / 2.54,
                "mm": TEX_PT_PER_INCH / 25.4, "pc": 12.0, "em": 10.0, "ex": 4.3}
DEFAULT_UNIT: Final = UNITS["cm"]
DEFAULT_LINE_WIDTH: Final = 0.4
LINE_WIDTHS: Final = {"ultra thin": 0.1, "very thin": 0.2, "thin": 0.4, "semithick": 0.6, "thick": 0.8,
                      "very thick": 1.2, "ultra thick": 1.6}
DASHES: Final = {"dashed": (3.0, 3.0), "densely dashed": (3.0, 2.0), "loosely dashed": (3.0, 6.0),
                 "dotted": (DEFAULT_LINE_WIDTH, 2.0), "densely dotted": (DEFAULT_LINE_WIDTH, 1.0),
                 "loosely dotted": (DEFAULT_LINE_WIDTH, 4.0), "solid": ()}
TIKZ_CAP_NAMES: Final = {"butt": "butt", "round": "round", "rect": "square"}
XCOLOR: Final = {
    "red": (1.0, 0.0, 0.0), "green": (0.0, 1.0, 0.0), "blue": (0.0, 0.0, 1.0), "cyan": (0.0, 1.0, 1.0),
    "magenta": (1.0, 0.0, 1.0), "yellow": (1.0, 1.0, 0.0), "black": BLACK, "white": (1.0, 1.0, 1.0),
    "gray": (0.5, 0.5, 0.5), "darkgray": (0.25, 0.25, 0.25), "lightgray": (0.75, 0.75, 0.75),
    "brown": (0.75, 0.5, 0.25), "lime": (0.75, 1.0, 0.0), "olive": (0.5, 0.5, 0.0), "orange": (1.0, 0.5, 0.0),
    "pink": (1.0, 0.75, 0.75), "purple": (0.75, 0.0, 0.25), "teal": (0.0, 0.5, 0.5), "violet": (0.5, 0.0, 0.5),
}
COMMAND_PAINTS: Final = {"draw": (False, True), "fill": (True, False), "filldraw": (True, True),
                         "path": (False, False), "useasboundingbox": (False, False)}
RGB_SCALE: Final = 255.0
PERCENT: Final = 100.0
FULL_TURN: Final = 2 * math.pi
COMMENT_RE: Final = re.compile(r"(?<!\\)%[^\n]*")
NODE_FONT_SIZE: Final = 10.0
NODE_BASELINE: Final = 0.35
NODE_TEXT_HEIGHT: Final = 0.8 * NODE_FONT_SIZE
INNER_SEP: Final = 3.333
MAX_STYLE_DEPTH: Final = 8
MAX_LOOPS: Final = 1000
MAX_LOOP_ITEMS: Final = 10000
DIAGONAL: Final = math.sqrt(0.5)
NODE_SHAPES: Final = ("circle", "rectangle", "ellipse")
ANCHORS: Final = {"center": (0, 0), "north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
                  "north east": (1, -1), "north west": (-1, -1), "south east": (1, 1), "south west": (-1, 1)}
POSITIONS: Final = {"above": "south", "below": "north", "left": "east", "right": "west",
                    "above left": "south east", "above right": "south west",
                    "below left": "north east", "below right": "north west"}
NODE_POSITIONS: Final = {"midway": 0.5, "near start": 0.25, "near end": 0.75, "very near start": 0.125,
                         "very near end": 0.875, "at start": 0.0, "at end": 1.0}
MARKUP_RE: Final = re.compile(r"\\[A-Za-z]+\*?\{([^{}]*)\}")
SPACE_RE: Final = re.compile(r"\s+")
EVENT_RE: Final = re.compile(r"\\(?:(begin|end)\s*\{scope\}|(filldraw|draw|fill|path|useasboundingbox|node|coordinate)"
                              r"(?![A-Za-z]))")
NODE_COMMANDS: Final = ("node", "coordinate")
FOREACH_RE: Final = re.compile(r"\\foreach\s+(\\[A-Za-z]+(?:\s*/\s*\\[A-Za-z]+)*)\s+in\s*")
MACRO_RE: Final = re.compile(r"\\[A-Za-z]+")
TIKZSET_RE: Final = re.compile(r"\\tikzset\s*\{")
TIKZSTYLE_RE: Final = re.compile(r"\\tikzstyle\s*\{([^}]*)\}\s*=\s*\[")
DEFINECOLOR_RE: Final = re.compile(r"\\definecolor\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{([^}]*)\}")
COLORLET_RE: Final = re.compile(r"\\colorlet\s*\{([^}]*)\}\s*\{([^}]*)\}")
PICTURE_RE: Final = re.compile(r"\\begin\s*\{tikzpicture\}")
DIMENSION_RE: Final = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*([a-z]{2})?\s*$")
PATH_TOKEN_RE: Final = re.compile(r"\s*(\+\+|\+|--|\|-|-\||\.\.|[A-Za-z]+|.)", re.S)
DASH_RE: Final = re.compile(r"(?:on|off)\s+([+-]?(?:\d+\.?\d*|\.\d+)\s*(?:[a-z]{2}(?![a-z]))?)")
BRACKETS: Final = {"(": ")", "[": "]", "{": "}"}
CLIP_TOLERANCE: Final = 1e-3
