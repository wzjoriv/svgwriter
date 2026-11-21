"""
Constants for ``svgwriter.model.color``: defaults, tables and patterns.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "A98_GAMMA",
    "A98_TO_XYZ",
    "ANGLE_UNITS",
    "BRADFORD_D50_TO_D65",
    "BRADFORD_D65_TO_D50",
    "CHANNEL_MAX",
    "COLOR_SPACES",
    "CONTRAST_OFFSET",
    "CONVERT_CACHE",
    "COORD_TOLERANCE",
    "CSS_FUNCTIONS",
    "CSS_SPACE_NAMES",
    "DE2000_L_MID",
    "DE2000_L_WIDTH",
    "DE2000_POW7",
    "DE2000_ROTATION_ANGLE",
    "DE2000_ROTATION_CENTRE",
    "DE2000_ROTATION_WIDTH",
    "DE2000_SC",
    "DE2000_SH",
    "DE2000_SL",
    "DE2000_T",
    "D50_WHITE",
    "DARK_LUMINANCE",
    "DEGREES",
    "FUNCTION_RE",
    "HEX_LONG",
    "HEX_SHORT",
    "IDENTITY",
    "ICC_RE",
    "LAB_EPSILON",
    "LAB_KAPPA",
    "LMS_TO_OKLAB",
    "LMS_TO_XYZ",
    "LUMA_WEIGHTS",
    "MIN_POSTERIZE_STEPS",
    "MIX_SPACES",
    "NAMED_TABLE",
    "OKLAB_TO_LMS",
    "P3_TO_XYZ",
    "PERCENT_MAX",
    "PERCENT_REFERENCE",
    "POLAR_SPACES",
    "REC2020_ALPHA",
    "REC2020_BETA",
    "REC2020_GAMMA",
    "REC2020_TO_XYZ",
    "SEPIA",
    "SRGB_DECODE_THRESHOLD",
    "SRGB_ENCODE_THRESHOLD",
    "SRGB_GAMMA",
    "SRGB_LINEAR_SLOPE",
    "SRGB_OFFSET",
    "SRGB_THRESHOLD",
    "SRGB_TO_XYZ",
    "XYZ_TO_LMS",
    "WHITE_POINT_ROOT",
    "XYZ_TO_SRGB",
]

NAMED_TABLE: Final = """
aliceblue f0f8ff antiquewhite faebd7 aqua 00ffff aquamarine 7fffd4
azure f0ffff beige f5f5dc bisque ffe4c4 black 000000 blanchedalmond ffebcd
blue 0000ff blueviolet 8a2be2 brown a52a2a burlywood deb887 cadetblue 5f9ea0
chartreuse 7fff00 chocolate d2691e coral ff7f50 cornflowerblue 6495ed
cornsilk fff8dc crimson dc143c cyan 00ffff darkblue 00008b darkcyan 008b8b
darkgoldenrod b8860b darkgray a9a9a9 darkgreen 006400 darkgrey a9a9a9
darkkhaki bdb76b darkmagenta 8b008b darkolivegreen 556b2f darkorange ff8c00
darkorchid 9932cc darkred 8b0000 darksalmon e9967a darkseagreen 8fbc8f
darkslateblue 483d8b darkslategray 2f4f4f darkslategrey 2f4f4f
darkturquoise 00ced1 darkviolet 9400d3 deeppink ff1493 deepskyblue 00bfff
dimgray 696969 dimgrey 696969 dodgerblue 1e90ff firebrick b22222
floralwhite fffaf0 forestgreen 228b22 fuchsia ff00ff gainsboro dcdcdc
ghostwhite f8f8ff gold ffd700 goldenrod daa520 gray 808080 grey 808080
green 008000 greenyellow adff2f honeydew f0fff0 hotpink ff69b4
indianred cd5c5c indigo 4b0082 ivory fffff0 khaki f0e68c lavender e6e6fa
lavenderblush fff0f5 lawngreen 7cfc00 lemonchiffon fffacd lightblue add8e6
lightcoral f08080 lightcyan e0ffff lightgoldenrodyellow fafad2
lightgray d3d3d3 lightgreen 90ee90 lightgrey d3d3d3 lightpink ffb6c1
lightsalmon ffa07a lightseagreen 20b2aa lightskyblue 87cefa
lightslategray 778899 lightslategrey 778899 lightsteelblue b0c4de
lightyellow ffffe0 lime 00ff00 limegreen 32cd32 linen faf0e6 magenta ff00ff
maroon 800000 mediumaquamarine 66cdaa mediumblue 0000cd mediumorchid ba55d3
mediumpurple 9370db mediumseagreen 3cb371 mediumslateblue 7b68ee
mediumspringgreen 00fa9a mediumturquoise 48d1cc mediumvioletred c71585
midnightblue 191970 mintcream f5fffa mistyrose ffe4e1 moccasin ffe4b5
navajowhite ffdead navy 000080 oldlace fdf5e6 olive 808000 olivedrab 6b8e23
orange ffa500 orangered ff4500 orchid da70d6 palegoldenrod eee8aa
palegreen 98fb98 paleturquoise afeeee palevioletred db7093
papayawhip ffefd5 peachpuff ffdab9 peru cd853f pink ffc0cb plum dda0dd
powderblue b0e0e6 purple 800080 red ff0000 rosybrown bc8f8f royalblue 4169e1
saddlebrown 8b4513 salmon fa8072 sandybrown f4a460 seagreen 2e8b57
seashell fff5ee sienna a0522d silver c0c0c0 skyblue 87ceeb slateblue 6a5acd
slategray 708090 slategrey 708090 snow fffafa springgreen 00ff7f
steelblue 4682b4 tan d2b48c teal 008080 thistle d8bfd8 tomato ff6347
turquoise 40e0d0 violet ee82ee wheat f5deb3 white ffffff whitesmoke f5f5f5
yellow ffff00 yellowgreen 9acd32
"""

CHANNEL_MAX: Final = 255
PERCENT_MAX: Final = 100.0
HEX_SHORT: Final = frozenset({3, 4})
HEX_LONG: Final = frozenset({6, 8})
DEGREES: Final = 360.0
SRGB_THRESHOLD: Final = 0.03928
SRGB_LINEAR_SLOPE: Final = 12.92
SRGB_OFFSET: Final = 0.055
SRGB_GAMMA: Final = 2.4
LUMA_WEIGHTS: Final = (0.2126, 0.7152, 0.0722)
FUNCTION_RE: Final = re.compile(r"^(rgba?|hsla?|hsva?|hwb|lab|lch|oklab|oklch|color|device-cmyk)\(\s*(.*?)\s*\)$")
ICC_RE: Final = re.compile(r"\s+(icc-color\([^)]*\))\s*$")

SRGB_DECODE_THRESHOLD: Final = 0.04045
SRGB_ENCODE_THRESHOLD: Final = 0.0031308
CONTRAST_OFFSET: Final = 0.05
DARK_LUMINANCE: Final = 0.179
"""Relative luminance below which black text has less contrast than white text."""

ANGLE_UNITS: Final = {"deg": 1.0, "grad": 0.9, "rad": 180.0 / 3.141592653589793, "turn": 360.0}
PERCENT_REFERENCE: Final = {
    "lab": (100.0, 125.0, 125.0), "lch": (100.0, 150.0, 1.0),
    "oklab": (1.0, 0.4, 0.4), "oklch": (1.0, 0.4, 1.0),
}
"""The value that 100% means for each channel of the CSS Color 4 lab-like functions."""
COLOR_SPACES: Final = frozenset({"srgb", "srgb-linear", "display-p3", "a98-rgb", "rec2020", "xyz", "xyz-d65",
                                 "xyz-d50"})
CSS_SPACE_NAMES: Final = {"xyz": "xyz-d65"}
"""``color()`` spaces CSS names differently from the colour space they mean."""
MIX_SPACES: Final = {"srgb": "srgb", "linear": "srgb-linear", "display-p3": "display-p3", "lab": "lab",
                     "lch": "lch", "oklab": "oklab", "oklch": "oklch", "xyz": "xyz-d65"}
"""Each mixing space name and the colour space it interpolates in."""
POLAR_SPACES: Final = frozenset({"lch", "oklch"})
"""Spaces whose third channel is a hue in degrees."""
CSS_FUNCTIONS: Final = frozenset({"lab", "lch", "oklab", "oklch"})
"""Spaces written by ``to_css`` as their own function rather than ``color(...)``."""
CONVERT_CACHE: Final = 4096
COORD_TOLERANCE: Final = 1e-6
"""How far outside ``0..1`` an sRGB channel may stray from rounding and still count as in gamut."""
WHITE_POINT_ROOT: Final = "xyz-d65"
"""The space every conversion passes through when no closer common space exists."""

SEPIA: Final = ((0.393, 0.769, 0.189), (0.349, 0.686, 0.168), (0.272, 0.534, 0.131))
"""The full-strength sepia matrix of the Filter Effects ``sepia()`` function."""
IDENTITY: Final = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
MIN_POSTERIZE_STEPS: Final = 2

DE2000_POW7: Final = 25.0 ** 7
DE2000_L_MID: Final = 50.0
DE2000_L_WIDTH: Final = 20.0
DE2000_SC: Final = 0.045
DE2000_SH: Final = 0.015
DE2000_SL: Final = 0.015
DE2000_T: Final = ((-0.17, 1.0, -30.0), (0.24, 2.0, 0.0), (0.32, 3.0, 6.0), (-0.20, 4.0, -63.0))
"""``(weight, multiple, offset)`` terms ``weight * cos(multiple * hue + offset)`` of the CIEDE2000 hue weighting ``T``."""
DE2000_ROTATION_CENTRE: Final = 275.0
DE2000_ROTATION_WIDTH: Final = 25.0
DE2000_ROTATION_ANGLE: Final = 60.0

LAB_KAPPA: Final = 24389 / 27
LAB_EPSILON: Final = 216 / 24389
D50_WHITE: Final = (0.3457 / 0.3585, 1.0, (1.0 - 0.3457 - 0.3585) / 0.3585)
A98_GAMMA: Final = 563 / 256
REC2020_ALPHA: Final = 1.09929682680944
REC2020_BETA: Final = 0.018053968510807
REC2020_GAMMA: Final = 1 / 0.45

SRGB_TO_XYZ: Final = ((0.41239079926595934, 0.357584339383878, 0.1804807884018343),
                      (0.21263900587151027, 0.715168678767756, 0.07219231536073371),
                      (0.01933081871559182, 0.11919477979462598, 0.9505321522496607))
XYZ_TO_SRGB: Final = ((3.2409699419045226, -1.537383177570094, -0.4986107602930034),
                      (-0.9692436362808796, 1.8759675015077202, 0.04155505740717559),
                      (0.05563007969699366, -0.20397695888897652, 1.0569715142428786))
P3_TO_XYZ: Final = ((0.4865709486482162, 0.26566769316909306, 0.1982172852343625),
                    (0.2289745640697488, 0.6917385218365064, 0.079286914093745),
                    (0.0, 0.04511338185890264, 1.043944368900976))
A98_TO_XYZ: Final = ((0.5766690429101305, 0.1855582379065463, 0.1882286462349947),
                     (0.29734497525053605, 0.6273635662554661, 0.0752914584939978),
                     (0.02703136138641234, 0.07068885253582723, 0.9913375368376388))
REC2020_TO_XYZ: Final = ((0.6369580483012914, 0.14461690358620832, 0.1688809751641721),
                         (0.2627002120112671, 0.6779980715188708, 0.05930171646986196),
                         (0.0, 0.028072693049087428, 1.060985057710791))
BRADFORD_D65_TO_D50: Final = ((1.0479298208405488, 0.022946793341019088, -0.05019222954313557),
                              (0.029627815688159344, 0.990434484573249, -0.01707382502938514),
                              (-0.009243058152591178, 0.015055144896577895, 0.7518742899580008))
BRADFORD_D50_TO_D65: Final = ((0.9554734527042182, -0.023098536874261423, 0.0632593086610217),
                              (-0.028369706963208136, 1.0099954580058226, 0.021041398966943008),
                              (0.012314001688319899, -0.020507696433477912, 1.3303659366080753))
XYZ_TO_LMS: Final = ((0.8190224379967030, 0.3619062600528904, -0.1288737815209879),
                     (0.0329836539323885, 0.9292868615863434, 0.0361446663506424),
                     (0.0481771893596242, 0.2642395317527308, 0.6335478284694309))
LMS_TO_XYZ: Final = ((1.2268798758459243, -0.5578149944602171, 0.2813910456659647),
                     (-0.0405757452148008, 1.1122868032803170, -0.0717110580655164),
                     (-0.0763729366746601, -0.4214933324022432, 1.5869240198367816))
LMS_TO_OKLAB: Final = ((0.2104542683093140, 0.7936177747023054, -0.0040720430116193),
                       (1.9779985324311684, -2.4285922420485799, 0.4505937096174110),
                       (0.0259040424655478, 0.7827717124575296, -0.8086757660377414))
OKLAB_TO_LMS: Final = ((1.0, 0.3963377773761749, 0.2158037573099136),
                       (1.0, -0.1055613458156586, -0.0638541728258133),
                       (1.0, -0.0894841775298119, -1.2914855480194092))
