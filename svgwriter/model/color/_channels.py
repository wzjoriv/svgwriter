"""
Channel views of a color: tuples, hex, HSL and luminance.
"""

from __future__ import annotations

import colorsys
from dataclasses import replace
from typing import TYPE_CHECKING

from ._constants import (
    CHANNEL_MAX,
    COORD_TOLERANCE,
    DEGREES,
    LUMA_WEIGHTS,
    SRGB_GAMMA,
    SRGB_LINEAR_SLOPE,
    SRGB_OFFSET,
    SRGB_THRESHOLD,
)
from ._spaces import Triple, convert

if TYPE_CHECKING:
    from .color import Color

__all__ = ["ColorChannels", "Source"]

Source = tuple[str, Triple]
"""A colour space name and the three channels a color was given in."""


class ColorChannels:
    """Read-only channel views shared by :class:`~svgwriter.model.color.Color`."""

    r: float
    g: float
    b: float
    a: float
    source: Source | None

    @property
    def space(self) -> str:
        """The colour space the color was given in: ``"srgb"``, or the space kept from CSS text or a mix.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color.parse("red").space, Color.parse("oklch(0.7 0.3 145)").space
        ('srgb', 'oklch')
        """
        return "srgb" if self.source is None else self.source[0]

    def coords(self, space: str | None = None) -> Triple:
        """The three channels in a colour space, unclipped.

        Parameters
        ----------
        space : str, optional
            ``"srgb"``, ``"srgb-linear"``, ``"display-p3"``, ``"a98-rgb"``, ``"rec2020"``,
            ``"xyz-d65"``, ``"xyz-d50"``, ``"lab"``, ``"lch"``, ``"oklab"`` or ``"oklch"``. Defaults
            to None, the color's own :attr:`space`.

        Returns
        -------
        tuple of float
            The channels, converted from the values the color was given in, so colors outside the
            sRGB gamut keep their real values. Lab and LCH use a D50 white with L in ``0..100``;
            hues are in degrees.

        Raises
        ------
        ValueError
            If `space` is unknown.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> [round(c, 4) for c in Color.parse("red").coords("display-p3")]
        [0.9175, 0.2003, 0.1386]
        >>> Color.parse("color(display-p3 1 0 0)").coords()
        (1.0, 0.0, 0.0)
        >>> [round(c, 3) for c in Color.parse("color(display-p3 1 0 0)").coords("srgb")]
        [1.093, -0.227, -0.15]
        """
        own, values = self.source or ("srgb", self.rgb)
        return values if space in (None, own) else convert(values, own, space)

    @property
    def in_gamut(self) -> bool:
        """Whether the color fits the sRGB gamut, so its sRGB output is exact rather than clipped.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color.parse("teal").in_gamut, Color.parse("color(display-p3 0 1 0)").in_gamut
        (True, False)
        """
        return all(-COORD_TOLERANCE <= c <= 1 + COORD_TOLERANCE for c in self.coords("srgb"))

    @property
    def rgb(self) -> tuple[float, float, float]:
        """The red, green and blue channels as floats in ``0..1``.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color(1, 0.5, 0).rgb
        (1, 0.5, 0)
        """
        return (self.r, self.g, self.b)

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        """The red, green, blue and alpha channels as floats in ``0..1``.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color(1, 0.5, 0).rgba
        (1, 0.5, 0, 1.0)
        """
        return (self.r, self.g, self.b, self.a)

    @property
    def uint8(self) -> tuple[int, int, int, int]:
        """RGBA as ``0..255`` integers.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color(1, 0.5, 0).uint8
        (255, 128, 0, 255)
        """
        return tuple(round(c * CHANNEL_MAX) for c in self.rgba)  # type: ignore[return-value]

    @property
    def hex(self) -> str:
        """The hex form: ``#rrggbb``, or ``#rrggbbaa`` when translucent.

        Examples
        --------
        >>> from svgwriter.model.color import Color
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
        >>> from svgwriter.model.color import Color
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
        >>> from svgwriter.model.color import Color
        >>> Color(1, 0, 0, 0.5).opaque.a
        1.0
        """
        return self if self.a == 1.0 else replace(self, a=1.0, name=None)

    @property
    def luminance(self) -> float:
        """Relative luminance per WCAG, from 0 (black) to 1 (white).

        Examples
        --------
        >>> from svgwriter.model.color import Color
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
