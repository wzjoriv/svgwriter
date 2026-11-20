"""
Channel views of a color: tuples, hex, HSL and luminance.
"""

from __future__ import annotations

import colorsys
from dataclasses import replace
from typing import TYPE_CHECKING

from ._constants import (
    CHANNEL_MAX,
    DEGREES,
    LUMA_WEIGHTS,
    SRGB_GAMMA,
    SRGB_LINEAR_SLOPE,
    SRGB_OFFSET,
    SRGB_THRESHOLD,
)

if TYPE_CHECKING:
    from .color import Color

__all__ = ["ColorChannels"]


class ColorChannels:
    """Read-only channel views shared by :class:`~svgwriter.color.Color`."""

    r: float
    g: float
    b: float
    a: float

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
