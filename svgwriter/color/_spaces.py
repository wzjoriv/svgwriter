"""
Colour-space conversions of CSS Color 4: sRGB transfer, XYZ, Lab/LCH, OKLab/OKLCH and the wide-gamut RGB spaces.
"""

from __future__ import annotations

import colorsys
import math
from collections.abc import Callable, Sequence

from ._constants import (
    A98_GAMMA,
    A98_TO_XYZ,
    BRADFORD_D50_TO_D65,
    D50_WHITE,
    DEGREES,
    LAB_EPSILON,
    LAB_KAPPA,
    LMS_TO_OKLAB,
    LMS_TO_XYZ,
    OKLAB_TO_LMS,
    P3_TO_XYZ,
    REC2020_ALPHA,
    REC2020_BETA,
    REC2020_GAMMA,
    REC2020_TO_XYZ,
    SRGB_DECODE_THRESHOLD,
    SRGB_ENCODE_THRESHOLD,
    SRGB_GAMMA,
    SRGB_LINEAR_SLOPE,
    SRGB_OFFSET,
    SRGB_TO_XYZ,
    XYZ_TO_LMS,
    XYZ_TO_SRGB,
)

__all__ = [
    "RGB_SPACES",
    "Triple",
    "cmyk_to_srgb",
    "hsv_to_srgb",
    "hwb_to_srgb",
    "lab_to_srgb",
    "lch_to_lab",
    "linear_to_srgb",
    "oklab_to_oklch",
    "oklab_to_srgb",
    "oklch_to_oklab",
    "srgb_to_linear",
    "srgb_to_oklab",
    "xyz_d65_to_srgb",
]

Triple = tuple[float, float, float]
REC2020_KNEE = REC2020_BETA * 4.5
REC2020_SLOPE = 4.5


def _apply(matrix: Sequence[Sequence[float]], values: Sequence[float]) -> Triple:
    r0, r1, r2 = (sum(m * v for m, v in zip(row, values, strict=True)) for row in matrix)
    return (r0, r1, r2)


def _signed(value: float, function: Callable[[float], float]) -> float:
    return math.copysign(function(abs(value)), value)


def srgb_to_linear(rgb: Sequence[float]) -> Triple:
    """Undo the sRGB transfer curve (also used by Display P3)."""

    def decode(c: float) -> float:
        return c / SRGB_LINEAR_SLOPE if c <= SRGB_DECODE_THRESHOLD else ((c + SRGB_OFFSET) / (1 + SRGB_OFFSET)) ** SRGB_GAMMA

    r, g, b = (_signed(c, decode) for c in rgb)
    return (r, g, b)


def linear_to_srgb(rgb: Sequence[float]) -> Triple:
    """Apply the sRGB transfer curve."""

    def encode(c: float) -> float:
        return c * SRGB_LINEAR_SLOPE if c <= SRGB_ENCODE_THRESHOLD else (1 + SRGB_OFFSET) * c ** (1 / SRGB_GAMMA) - SRGB_OFFSET

    r, g, b = (_signed(c, encode) for c in rgb)
    return (r, g, b)


def xyz_d65_to_srgb(xyz: Sequence[float]) -> Triple:
    """CIE XYZ (D65) to gamma-encoded sRGB, unclipped."""
    return linear_to_srgb(_apply(XYZ_TO_SRGB, xyz))


def _xyz_d50_to_srgb(xyz: Sequence[float]) -> Triple:
    return xyz_d65_to_srgb(_apply(BRADFORD_D50_TO_D65, xyz))


def _rec2020_decode(c: float) -> float:
    return c / REC2020_SLOPE if c < REC2020_KNEE else ((c + REC2020_ALPHA - 1) / REC2020_ALPHA) ** REC2020_GAMMA


def _rgb_space(matrix: Sequence[Sequence[float]], decode: Callable[[Sequence[float]], Triple]) -> Callable[[Sequence[float]], Triple]:
    return lambda rgb: xyz_d65_to_srgb(_apply(matrix, decode(rgb)))


RGB_SPACES: dict[str, Callable[[Sequence[float]], Triple]] = {
    "srgb": lambda rgb: (rgb[0], rgb[1], rgb[2]),
    "srgb-linear": linear_to_srgb,
    "display-p3": _rgb_space(P3_TO_XYZ, srgb_to_linear),
    "a98-rgb": _rgb_space(A98_TO_XYZ, lambda rgb: tuple(_signed(c, lambda v: v ** A98_GAMMA) for c in rgb)),  # type: ignore[arg-type, return-value]
    "rec2020": _rgb_space(REC2020_TO_XYZ, lambda rgb: tuple(_signed(c, _rec2020_decode) for c in rgb)),  # type: ignore[arg-type, return-value]
    "xyz": xyz_d65_to_srgb,
    "xyz-d65": xyz_d65_to_srgb,
    "xyz-d50": _xyz_d50_to_srgb,
}
"""``color(<space> r g b)``: each space's channels to gamma-encoded sRGB, unclipped."""


def lab_to_srgb(lab: Sequence[float]) -> Triple:
    """CIE Lab (D50, L in 0..100) to gamma-encoded sRGB, unclipped."""
    lightness, a, b = lab
    fy = (lightness + 16) / 116
    fx, fz = a / 500 + fy, fy - b / 200
    x = fx ** 3 if fx ** 3 > LAB_EPSILON else (116 * fx - 16) / LAB_KAPPA
    y = fy ** 3 if lightness > LAB_KAPPA * LAB_EPSILON else lightness / LAB_KAPPA
    z = fz ** 3 if fz ** 3 > LAB_EPSILON else (116 * fz - 16) / LAB_KAPPA
    return _xyz_d50_to_srgb((x * D50_WHITE[0], y * D50_WHITE[1], z * D50_WHITE[2]))


def lch_to_lab(lch: Sequence[float]) -> Triple:
    """Polar LCH (hue in degrees) to rectangular Lab; the same for OKLCH to OKLab."""
    lightness, chroma, hue = lch
    angle = math.radians(hue)
    return (lightness, chroma * math.cos(angle), chroma * math.sin(angle))


oklch_to_oklab = lch_to_lab


def oklab_to_srgb(oklab: Sequence[float]) -> Triple:
    """OKLab (L in 0..1) to gamma-encoded sRGB, unclipped."""
    lms = tuple(c ** 3 for c in _apply(OKLAB_TO_LMS, oklab))
    return xyz_d65_to_srgb(_apply(LMS_TO_XYZ, lms))


def srgb_to_oklab(rgb: Sequence[float]) -> Triple:
    """Gamma-encoded sRGB to OKLab."""
    lms = _apply(XYZ_TO_LMS, _apply(SRGB_TO_XYZ, srgb_to_linear(rgb)))
    return _apply(LMS_TO_OKLAB, tuple(math.copysign(abs(c) ** (1 / 3), c) for c in lms))


def oklab_to_oklch(oklab: Sequence[float]) -> Triple:
    """OKLab to OKLCH with the hue in degrees."""
    lightness, a, b = oklab
    return (lightness, math.hypot(a, b), math.degrees(math.atan2(b, a)) % DEGREES)


def hwb_to_srgb(hue: float, white: float, black: float) -> Triple:
    """HWB (hue in degrees, whiteness and blackness in 0..1) to sRGB."""
    if white + black >= 1:
        grey = white / (white + black)
        return (grey, grey, grey)
    r, g, b = colorsys.hls_to_rgb((hue % DEGREES) / DEGREES, 0.5, 1.0)
    return (r * (1 - white - black) + white, g * (1 - white - black) + white, b * (1 - white - black) + white)


def hsv_to_srgb(hue: float, saturation: float, value: float) -> Triple:
    """HSV (hue in degrees, saturation and value in 0..1) to sRGB."""
    return colorsys.hsv_to_rgb((hue % DEGREES) / DEGREES, saturation, value)


def cmyk_to_srgb(cyan: float, magenta: float, yellow: float, black: float) -> Triple:
    """The naive ``device-cmyk`` conversion of CSS Color 5: no profile, ink limits or black generation."""
    r, g, b = (1 - min(1.0, c * (1 - black) + black) for c in (cyan, magenta, yellow))
    return (r, g, b)
