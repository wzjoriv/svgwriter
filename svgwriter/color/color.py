"""
RGBA colors with channels in ``0..1`` and the SVG/CSS color syntaxes.
"""

from __future__ import annotations

import colorsys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field, replace
from functools import lru_cache
from numbers import Real
from typing import Any, TypeAlias

import numpy as np

from .._internal._constants import DEFAULT_PRECISION
from .._internal._drawable import Drawable, color_swatch
from .._internal._numbers import format_number
from .._internal._typing import N, Opacity
from ._constants import (
    CHANNEL_MAX,
    DEGREES,
    FUNCTION_RE,
    HEX_LONG,
    HEX_SHORT,
    ICC_RE,
    LUMA_WEIGHTS,
    PERCENT_MAX,
    SRGB_GAMMA,
    SRGB_LINEAR_SLOPE,
    SRGB_OFFSET,
    SRGB_THRESHOLD,
)
from ._named import COLOR_ALIASES, NAMED_COLORS

__all__ = ["Color", "ColorLike", "as_color", "clamp", "parse_color"]


def clamp(value: N, low: N, high: N) -> N:
    """Clamp a value into a range.

    Parameters
    ----------
    value : int or float
        The value to clamp.
    low, high : int or float
        Lower and upper bounds, inclusive.

    Returns
    -------
    int or float
        `low` if `value` is below it, `high` if above, otherwise `value`.

    Examples
    --------
    >>> from svgwriter.color import clamp
    >>> clamp(5, 0, 1)
    1
    >>> clamp(-0.5, 0.0, 1.0)
    0.0
    """
    return max(low, min(high, value))


@dataclass(frozen=True)
class Color(Drawable):
    """An sRGB color with straight alpha; every channel is a float in ``0..1``.

    Colors are immutable, support ``+`` (even mix), ``*`` and ``/`` (scaling),
    and iterate as ``r, g, b, a``.

    Parameters
    ----------
    r, g, b : float
        Red, green and blue in ``0..1``.
    a : float, optional
        Alpha (opacity) in ``0..1``; 1 is opaque. Defaults to 1.0.
    icc : str, optional
        An ``icc-color(...)`` specification kept alongside the sRGB value. Defaults to None.
    name : str, optional
        Keyword written instead of hex (set when parsed from a name); ignored
        when comparing. Defaults to None.

    Raises
    ------
    ValueError
        If any channel is outside ``0..1``.

    See Also
    --------
    as_color : Coerce names, tuples and colors into a `Color`.
    parse_color : Parse CSS color text.

    Notes
    -----
    Everything that takes a color also takes a :data:`ColorLike`: a name or
    CSS string, a ``Color``, or a 3/4-tuple of floats in ``0..1`` (as in
    matplotlib). Use :meth:`from_uint8` for ``0..255`` values. SVG 1.1 has
    no alpha in colors, so a translucent ``fill``/``stroke``/``stop-color``/
    ``flood-color`` also writes the matching ``*-opacity`` attribute.

    Examples
    --------
    >>> from svgwriter.color import Color
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
        """Parse a name, ``#rgb[a]``, ``#rrggbb[aa]``, ``rgb[a](...)`` or ``hsl[a](...)``.

        Parameters
        ----------
        text : str
            Color text.

        Returns
        -------
        Color
            The parsed color.

        Raises
        ------
        ValueError
            If the text is not a recognized color.

        See Also
        --------
        parse_color : The equivalent function.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#f80").hex
        '#ff8800'
        """
        return parse_color(text)

    @classmethod
    def from_uint8(cls, r: int, g: int, b: int, a: int = CHANNEL_MAX) -> Color:
        """Build a color from ``0..255`` channels.

        Parameters
        ----------
        r, g, b : int
            Red, green and blue; clamped to ``0..255``.
        a : int, optional
            Alpha; clamped to ``0..255``. Defaults to 255 (opaque).

        Returns
        -------
        Color
            The color with channels scaled to ``0..1``.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.from_uint8(255, 0, 0).hex
        '#ff0000'
        """
        return cls(*(clamp(int(c), 0, CHANNEL_MAX) / CHANNEL_MAX for c in (r, g, b, a)))

    @classmethod
    def from_hsl(cls, hue: float, saturation: float, lightness: float, alpha: float = 1.0) -> Color:
        """Build a color from hue, saturation and lightness.

        Parameters
        ----------
        hue : float
            Hue in degrees; wrapped into ``0..360``.
        saturation, lightness : float
            Saturation and lightness in ``0..1``.
        alpha : float, optional
            Opacity in ``0..1``. Defaults to 1.0.

        Returns
        -------
        Color
            The corresponding sRGB color.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.from_hsl(240, 1, 0.5).hex
        '#0000ff'
        """
        r, g, b = colorsys.hls_to_rgb((hue % DEGREES) / DEGREES, lightness, saturation)
        return cls(r, g, b, alpha)

    @property
    def rgb(self) -> tuple[float, float, float]:
        """The red, green and blue channels as floats in ``0..1``.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(1, 0.5, 0).rgb
        (1, 0.5, 0)
        """
        return (self.r, self.g, self.b)

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        """The red, green, blue and alpha channels as floats in ``0..1``.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(1, 0.5, 0).rgba
        (1, 0.5, 0, 1.0)
        """
        return (self.r, self.g, self.b, self.a)

    @property
    def uint8(self) -> tuple[int, int, int, int]:
        """RGBA as ``0..255`` integers.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(1, 0.5, 0).uint8
        (255, 128, 0, 255)
        """
        return tuple(round(c * CHANNEL_MAX) for c in self.rgba)  # type: ignore[return-value]

    @property
    def hex(self) -> str:
        """The hex form: ``#rrggbb``, or ``#rrggbbaa`` when translucent.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(1, 0.5, 0).hex
        '#ff8000'
        >>> Color(1, 0, 0, 0.5).hex
        '#ff000080'
        """
        r, g, b, a = self.uint8
        return f"#{r:02x}{g:02x}{b:02x}" + (f"{a:02x}" if a < CHANNEL_MAX else "")

    @property
    def hsl(self) -> tuple[float, float, float]:
        """Hue in degrees, saturation and lightness in ``0..1``.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("blue").hsl
        (240.0, 1.0, 0.5)
        """
        h, light, s = colorsys.rgb_to_hls(*self.rgb)
        return (h * DEGREES, s, light)

    @property
    def opaque(self) -> Color:
        """This color with alpha 1.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(1, 0, 0, 0.5).opaque.a
        1.0
        """
        return self if self.a == 1.0 else replace(self, a=1.0, name=None)

    @property
    def luminance(self) -> float:
        """Relative luminance per WCAG, from 0 (black) to 1 (white).

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("black").luminance
        0.0
        >>> round(Color.parse("white").luminance, 6)
        1.0
        """

        def linear(v: float) -> float:
            if v <= SRGB_THRESHOLD:
                return v / SRGB_LINEAR_SLOPE
            return ((v + SRGB_OFFSET) / (1 + SRGB_OFFSET)) ** SRGB_GAMMA

        return sum(w * linear(c) for w, c in zip(LUMA_WEIGHTS, self.rgb, strict=True))

    def with_alpha(self, alpha: Opacity) -> Color:
        """Return the same color with a different alpha.

        Parameters
        ----------
        alpha : float
            New opacity in ``0..1``.

        Returns
        -------
        Color
            A copy with the given alpha.

        Raises
        ------
        ValueError
            If `alpha` is outside ``0..1``.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").with_alpha(0.5).a
        0.5
        """
        return replace(self, a=float(alpha), name=None if alpha != 1 else self.name)

    def lighten(self, amount: Opacity) -> Color:
        """Raise HSL lightness by an amount.

        Parameters
        ----------
        amount : float
            Change in lightness on a ``0..1`` scale; negative darkens. The result is clamped.

        Returns
        -------
        Color
            The adjusted color.

        See Also
        --------
        darken : Lower lightness instead.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(0.5, 0.5, 0.5).lighten(0.2).hex
        '#b2b2b2'
        """
        h, s, light = self.hsl
        return Color.from_hsl(h, s, clamp(light + amount, 0.0, 1.0), self.a)

    def darken(self, amount: Opacity) -> Color:
        """Lower HSL lightness by an amount.

        Parameters
        ----------
        amount : float
            Decrease in lightness on a ``0..1`` scale.

        Returns
        -------
        Color
            The adjusted color.

        See Also
        --------
        lighten : Raise lightness instead.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(0.5, 0.5, 0.5).darken(0.2).hex
        '#4c4c4c'
        """
        return self.lighten(-amount)

    def mix(self, other: ColorLike, weight: Opacity = 0.5) -> Color:
        """Blend linearly with another color.

        Parameters
        ----------
        other : Color or str or sequence of float
            The color to mix in.
        weight : float, optional
            Share of `other` in the result, from 0 to 1. Defaults to 0.5.

        Returns
        -------
        Color
            The blended color; alpha is blended too.

        Raises
        ------
        ValueError
            If `other` is not a valid color.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").mix("blue", 0.25).hex
        '#bf0040'
        """
        other = as_color(other)
        return Color(*(a + (b - a) * weight for a, b in zip(self.rgba, other.rgba, strict=True)))

    def scale(self, factor: float) -> Color:
        """Multiply the color channels by a factor.

        Alpha is unchanged and channels are clamped to ``0..1``.

        Parameters
        ----------
        factor : float
            Multiplier; above 1 brightens, below 1 darkens.

        Returns
        -------
        Color
            The scaled color.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(0.5, 0.2, 0.1).scale(2).hex
        '#ff6633'
        """
        return Color(*(clamp(c * factor, 0.0, 1.0) for c in self.rgb), self.a)

    def __add__(self, other: ColorLike) -> Color:
        """Mix evenly with another color (``color + other``)."""
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
        """Return ``[r, g, b, a]`` as floats in ``0..1`` for NumPy."""
        return np.array(self.rgba, dtype=dtype or np.float64)

    def with_icc(self, spec: str) -> Color:
        """Return the color with an ICC specification attached.

        Parameters
        ----------
        spec : str
            An ``icc-color(...)`` specification, written after the sRGB fallback.

        Returns
        -------
        Color
            A copy carrying the specification.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").with_icc("icc-color(profile, 1)").svg_value()
        'red icc-color(profile, 1)'
        """
        return replace(self, icc=spec)

    def to_css(self) -> str:
        """Return CSS text for the color.

        Returns
        -------
        str
            The name or hex when opaque, ``rgba(...)`` otherwise.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").to_css()
        'red'
        >>> Color(1, 0, 0, 0.5).to_css()
        'rgba(255, 0, 0, 0.5)'
        """
        if self.a == 1.0:
            return self.name or self.hex
        r, g, b, _ = self.uint8
        return f"rgba({r}, {g}, {b}, {format_number(self.a, DEFAULT_PRECISION)})"

    def __svgwriter__(self) -> Any:
        """A swatch of this color over a checkerboard (``doc.add(color)``, notebook display)."""
        return color_swatch(self)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Return SVG 1.1 color text.

        The name or ``#rrggbb`` is written; alpha is not part of the text and
        is emitted separately as an opacity attribute.

        Parameters
        ----------
        precision : int, optional
            Unused; accepted for a uniform interface. Defaults to the library default precision.

        Returns
        -------
        str
            The color text, followed by any ICC specification.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(1, 0, 0, 0.5).svg_value()
        '#ff0000'
        """
        text = self.name if self.name and self.a == 1.0 else self.opaque.hex
        return f"{text} {self.icc}" if self.icc else text

    def __str__(self) -> str:
        return self.svg_value()


ColorLike: TypeAlias = Color | str | Sequence[float]
"""A ``Color``, a color string, or a 3/4-sequence of floats in ``0..1``."""


def as_color(value: ColorLike) -> Color:
    """Coerce a :data:`ColorLike` into a :class:`Color`.

    Parameters
    ----------
    value : Color or str or sequence of float
        A color, color text, or a 3- or 4-sequence of floats in ``0..1``.

    Returns
    -------
    Color
        `value` itself if it is already a `Color`.

    Raises
    ------
    ValueError
        For unknown names or channels outside ``0..1``.
    TypeError
        For anything that is not a color.

    See Also
    --------
    parse_color : Parse text only.

    Examples
    --------
    >>> from svgwriter.color import as_color
    >>> as_color("blue").hex
    '#0000ff'
    >>> as_color((1, 0, 0)).hex
    '#ff0000'
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

    An optional trailing ``icc-color(...)`` is preserved. Results are cached.

    Parameters
    ----------
    text : str
        Color text such as ``"tomato"``, ``"#f80"``, ``"rgb(255 0 0)"`` or ``"hsl(120, 100%, 50%)"``.

    Returns
    -------
    Color
        The parsed color.

    Raises
    ------
    ValueError
        If the text is not a recognized color.

    See Also
    --------
    as_color : Also accepts colors and channel sequences.

    Examples
    --------
    >>> from svgwriter.color import parse_color
    >>> parse_color("tomato").uint8
    (255, 99, 71, 255)
    >>> parse_color("hsl(120, 100%, 50%)").hex
    '#00ff00'
    """
    source = text.strip()
    icc = None
    match = ICC_RE.search(source)
    if match:
        icc = match.group(1)
        source = source[: match.start()]
    lowered = COLOR_ALIASES.get(source.lower(), source.lower())
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
    function = FUNCTION_RE.match(lowered)
    if function:
        return replace(_function(function.group(1), function.group(2), text), icc=icc)
    raise ValueError(f"unknown color: {text!r}")
