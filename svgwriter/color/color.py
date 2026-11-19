"""RGBA colors with channels in ``0..1`` and the SVG/CSS color syntaxes."""

from __future__ import annotations

import colorsys
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, replace
from functools import lru_cache
from numbers import Real
from typing import Final, TypeAlias

import numpy as np

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number
from .._internal._typing import N, Opacity
from ._named import NAMED_COLORS

__all__ = ["Color", "ColorLike", "as_color", "clamp", "parse_color"]

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

_FUNCTION_RE: Final = re.compile(r"^(rgba?|hsla?)\(\s*(.*?)\s*\)$")
_ICC_RE: Final = re.compile(r"\s+(icc-color\([^)]*\))\s*$")


def clamp(value: N, low: N, high: N) -> N:
    """Clamp *value* into ``[low, high]``."""
    return max(low, min(high, value))


@dataclass(frozen=True)
class Color:
    """An sRGB color with straight alpha; every channel is a float in ``0..1``.

    Parameters
    ----------
    r, g, b : float
        Red, green and blue in ``0..1``.
    a : float
        Alpha (opacity) in ``0..1``; 1 is opaque.
    icc : str, optional
        An ``icc-color(...)`` specification kept alongside the sRGB value.
    name : str, optional
        Keyword written instead of hex (set when parsed from a name).

    Examples
    --------
    >>> Color(1, 0.5, 0).hex
    '#ff8000'
    >>> Color.parse("#f80").uint8
    (255, 136, 0, 255)
    >>> Color.from_uint8(255, 0, 0, 128).a
    0.5019607843137255
    >>> str(Color.parse("red") + "blue")
    '#800080'
    >>> Color.parse("rgba(0, 0, 255, 0.25)").a
    0.25

    Notes
    -----
    Everything that takes a color also takes a :data:`ColorLike`: a name or
    CSS string, a ``Color``, or a 3/4-tuple of floats in ``0..1`` (as in
    matplotlib). Use :meth:`from_uint8` for ``0..255`` values. SVG 1.1 has
    no alpha in colors, so a translucent ``fill``/``stroke``/``stop-color``/
    ``flood-color`` also writes the matching ``*-opacity`` attribute.
    """

    r: float
    g: float
    b: float
    a: float = 1.0
    icc: str | None = None
    name: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        for label, value in zip("rgba", (self.r, self.g, self.b, self.a), strict=True):
            if not 0.0 <= value <= 1.0:
                hint = "; use Color.from_uint8 for 0..255 values" if value > 1 else ""
                raise ValueError(f"channel {label}={value} is outside 0..1{hint}")

    @classmethod
    def parse(cls, text: str) -> Color:
        """Parse a name, ``#rgb[a]``, ``#rrggbb[aa]``, ``rgb[a](...)`` or ``hsl[a](...)``."""
        return parse_color(text)

    @classmethod
    def from_uint8(cls, r: int, g: int, b: int, a: int = CHANNEL_MAX) -> Color:
        """Build from ``0..255`` channels."""
        return cls(*(clamp(int(c), 0, CHANNEL_MAX) / CHANNEL_MAX for c in (r, g, b, a)))

    @classmethod
    def from_hsl(cls, hue: float, saturation: float, lightness: float, alpha: float = 1.0) -> Color:
        """Build from hue in degrees and saturation, lightness and alpha in ``0..1``."""
        r, g, b = colorsys.hls_to_rgb((hue % DEGREES) / DEGREES, lightness, saturation)
        return cls(r, g, b, alpha)

    @property
    def rgb(self) -> tuple[float, float, float]:
        return (self.r, self.g, self.b)

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        return (self.r, self.g, self.b, self.a)

    @property
    def uint8(self) -> tuple[int, int, int, int]:
        """RGBA as ``0..255`` integers."""
        return tuple(round(c * CHANNEL_MAX) for c in self.rgba)  # type: ignore[return-value]

    @property
    def hex(self) -> str:
        """``#rrggbb``, or ``#rrggbbaa`` when translucent."""
        r, g, b, a = self.uint8
        return f"#{r:02x}{g:02x}{b:02x}" + (f"{a:02x}" if a < CHANNEL_MAX else "")

    @property
    def hsl(self) -> tuple[float, float, float]:
        """Hue in degrees, saturation and lightness in ``0..1``."""
        h, light, s = colorsys.rgb_to_hls(*self.rgb)
        return (h * DEGREES, s, light)

    @property
    def opaque(self) -> Color:
        """This color with alpha 1."""
        return self if self.a == 1.0 else replace(self, a=1.0, name=None)

    @property
    def luminance(self) -> float:
        """Relative luminance per WCAG."""

        def linear(v: float) -> float:
            if v <= SRGB_THRESHOLD:
                return v / SRGB_LINEAR_SLOPE
            return ((v + SRGB_OFFSET) / (1 + SRGB_OFFSET)) ** SRGB_GAMMA

        return sum(w * linear(c) for w, c in zip(LUMA_WEIGHTS, self.rgb, strict=True))

    def with_alpha(self, alpha: Opacity) -> Color:
        """The same color with alpha *alpha*."""
        return replace(self, a=float(alpha), name=None if alpha != 1 else self.name)

    def lighten(self, amount: Opacity) -> Color:
        """Raise HSL lightness by *amount* (negative darkens)."""
        h, s, light = self.hsl
        return Color.from_hsl(h, s, clamp(light + amount, 0.0, 1.0), self.a)

    def darken(self, amount: Opacity) -> Color:
        return self.lighten(-amount)

    def mix(self, other: ColorLike, weight: Opacity = 0.5) -> Color:
        """Linear blend of every channel; *weight* is the share of *other*."""
        other = as_color(other)
        return Color(*(a + (b - a) * weight for a, b in zip(self.rgba, other.rgba, strict=True)))

    def scale(self, factor: float) -> Color:
        """Multiply the color channels (not alpha) by *factor*, clamped to ``0..1``."""
        return Color(*(clamp(c * factor, 0.0, 1.0) for c in self.rgb), self.a)

    def __add__(self, other: ColorLike) -> Color:
        """Even mix."""
        try:
            return self.mix(other)
        except (TypeError, ValueError):
            return NotImplemented

    def __radd__(self, other: ColorLike) -> Color:
        try:
            return as_color(other).mix(self)
        except (TypeError, ValueError):
            return NotImplemented

    def __mul__(self, factor: float | Color) -> Color:
        """Scale by a number, or multiply channel-wise by another color."""
        if isinstance(factor, Color):
            return Color(*(a * b for a, b in zip(self.rgba, factor.rgba, strict=True)))
        if isinstance(factor, Real):
            return self.scale(float(factor))
        return NotImplemented

    def __rmul__(self, factor: float) -> Color:
        return self.scale(float(factor)) if isinstance(factor, Real) else NotImplemented

    def __truediv__(self, divisor: float) -> Color:
        return self.scale(1.0 / divisor) if isinstance(divisor, Real) else NotImplemented

    def __iter__(self) -> Iterator[float]:
        return iter(self.rgba)

    def __array__(self, dtype: object = None, copy: object = None) -> np.ndarray:
        """``[r, g, b, a]`` as floats in ``0..1``."""
        return np.array(self.rgba, dtype=dtype or np.float64)

    def with_icc(self, spec: str) -> Color:
        return replace(self, icc=spec)

    def to_css(self) -> str:
        """CSS text: the name or hex when opaque, ``rgba(...)`` otherwise."""
        if self.a == 1.0:
            return self.name or self.hex
        r, g, b, _ = self.uint8
        return f"rgba({r}, {g}, {b}, {format_number(self.a, DEFAULT_PRECISION)})"

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """SVG 1.1 text (name or ``#rrggbb``); alpha is written separately as an opacity."""
        text = self.name if self.name and self.a == 1.0 else self.opaque.hex
        return f"{text} {self.icc}" if self.icc else text

    def __str__(self) -> str:
        return self.svg_value()


ColorLike: TypeAlias = Color | str | Sequence[float]
"""A ``Color``, a color string, or a 3/4-sequence of floats in ``0..1``."""


def as_color(value: ColorLike) -> Color:
    """Coerce a :data:`ColorLike` into a :class:`Color`.

    Raises
    ------
    ValueError
        For unknown names or channels outside ``0..1``.
    TypeError
        For anything that is not a color.
    """
    if isinstance(value, Color):
        return value
    if isinstance(value, str):
        return parse_color(value)
    try:
        channels = [float(c) for c in value]
    except TypeError:
        raise TypeError(f"expected a color, got {type(value).__name__}") from None
    if len(channels) not in (3, 4):
        raise ValueError(f"a color needs 3 or 4 channels, got {len(channels)}")
    return Color(*channels)


def _channel(token: str) -> float:
    if token.endswith("%"):
        return clamp(float(token[:-1]) / PERCENT_MAX, 0.0, 1.0)
    return clamp(float(token) / CHANNEL_MAX, 0.0, 1.0)


def _alpha(token: str) -> float:
    value = float(token[:-1]) / PERCENT_MAX if token.endswith("%") else float(token)
    return clamp(value, 0.0, 1.0)


def _function(kind: str, body: str, text: str) -> Color:
    if "/" in body:
        main, _, alpha_text = body.partition("/")
        tokens = main.replace(",", " ").split() + [alpha_text.strip()]
    else:
        tokens = body.replace(",", " ").split()
    if len(tokens) not in (3, 4):
        raise ValueError(f"invalid color: {text!r}")
    alpha = _alpha(tokens[3]) if len(tokens) == 4 else 1.0
    if kind.startswith("hsl"):
        hue = float(tokens[0].removesuffix("deg"))
        return Color.from_hsl(hue, _alpha(tokens[1]), _alpha(tokens[2]), alpha)
    if len({t.endswith("%") for t in tokens[:3]}) != 1:
        raise ValueError(f"mixed number and percent channels: {text!r}")
    return Color(*(_channel(t) for t in tokens[:3]), alpha)


@lru_cache(maxsize=256)
def parse_color(text: str) -> Color:
    """Parse a color keyword, hex, ``rgb[a](...)`` or ``hsl[a](...)``.

    An optional trailing ``icc-color(...)`` is preserved.

    Examples
    --------
    >>> parse_color("tomato").uint8
    (255, 99, 71, 255)
    >>> parse_color("hsl(120, 100%, 50%)").hex
    '#00ff00'
    """
    source = text.strip()
    icc = None
    match = _ICC_RE.search(source)
    if match:
        icc = match.group(1)
        source = source[: match.start()]
    lowered = source.lower()
    if lowered in NAMED_COLORS:
        r, g, b = NAMED_COLORS[lowered]
        return replace(Color.from_uint8(r, g, b), icc=icc, name=lowered)
    if lowered.startswith("#"):
        digits = lowered[1:]
        if len(digits) in HEX_SHORT:
            digits = "".join(d * 2 for d in digits)
        if len(digits) not in HEX_LONG or any(d not in "0123456789abcdef" for d in digits):
            raise ValueError(f"invalid hex color: {text!r}")
        channels = [int(digits[i:i + 2], 16) for i in range(0, len(digits), 2)]
        return replace(Color.from_uint8(*channels), icc=icc)
    function = _FUNCTION_RE.match(lowered)
    if function:
        return replace(_function(function.group(1), function.group(2), text), icc=icc)
    raise ValueError(f"unknown color: {text!r}")
