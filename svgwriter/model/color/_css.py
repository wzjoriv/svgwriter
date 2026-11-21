"""
Color text: SVG 1.1 values, ICC specifications and CSS Color 4 in any space.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Literal, TypeAlias

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number
from ._channels import ColorChannels
from ._constants import CSS_FUNCTIONS, DEGREES

if TYPE_CHECKING:
    from .color import Color

__all__ = ["ColorText", "CssSpace"]

CssSpace: TypeAlias = Literal["srgb", "hsl", "hwb", "lab", "lch", "oklab", "oklch", "srgb-linear", "display-p3",
                              "a98-rgb", "rec2020", "xyz-d65", "xyz-d50"]


class ColorText(ColorChannels):
    """SVG and CSS text shared by :class:`~svgwriter.model.color.Color`."""

    icc: str | None
    name: str | None

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
        >>> from svgwriter.model.color import Color
        >>> Color.parse("red").with_icc("icc-color(profile, 1)").svg_value()
        'red icc-color(profile, 1)'
        """
        return replace(self, icc=spec)  # type: ignore[type-var]

    def to_css(self, space: CssSpace = "srgb", precision: int = DEFAULT_PRECISION) -> str:
        """Return CSS text for the color in a chosen space.

        Parameters
        ----------
        space : str, optional
            ``"srgb"`` writes the name or hex when opaque and ``rgba(...)`` otherwise, clipped to the
            sRGB gamut. ``"hsl"`` and ``"hwb"`` write those sRGB functions. ``"lab"``, ``"lch"``,
            ``"oklab"`` and ``"oklch"`` write their own functions and ``"srgb-linear"``,
            ``"display-p3"``, ``"a98-rgb"``, ``"rec2020"``, ``"xyz-d65"`` and ``"xyz-d50"`` write
            ``color(<space> ...)``; these keep colours outside the sRGB gamut. Defaults to ``"srgb"``.
        precision : int, optional
            Decimals of each channel. Defaults to the library default precision.

        Returns
        -------
        str
            The CSS color; a translucent color ends with ``/ alpha`` in every space but ``"srgb"``.

        Raises
        ------
        ValueError
            If `space` is unknown.

        See Also
        --------
        coords : The channels themselves.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color.parse("red").to_css()
        'red'
        >>> Color(1, 0, 0, 0.5).to_css()
        'rgba(255, 0, 0, 0.5)'
        >>> Color.parse("red").to_css("oklch", precision=2)
        'oklch(0.63 0.26 29.23)'
        >>> Color.parse("color(display-p3 1 0 0)").to_css("display-p3")
        'color(display-p3 1 0 0)'
        >>> Color.parse("blue").with_alpha(0.5).to_css("hsl")
        'hsl(240 100% 50% / 0.5)'
        """
        if space == "srgb":
            if self.a == 1.0:
                return self.name or self.hex
            r, g, b, _ = self.uint8
            return f"rgba({r}, {g}, {b}, {format_number(self.a, precision)})"
        alpha = "" if self.a == 1.0 else f" / {format_number(self.a, precision)}"
        if space in ("hsl", "hwb"):
            hue, saturation, lightness = self.hsl
            second, third = (saturation, lightness) if space == "hsl" else (min(self.rgb), 1 - max(self.rgb))
            values = [format_number(hue % DEGREES, precision),
                      *(f"{format_number(c * 100, precision)}%" for c in (second, third))]
            return f"{space}({' '.join(values)}{alpha})"
        channels = " ".join(format_number(c, precision) for c in self.coords(space))
        if space in CSS_FUNCTIONS:
            return f"{space}({channels}{alpha})"
        return f"color({space} {channels}{alpha})"

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
        >>> from svgwriter.model.color import Color
        >>> Color(1, 0, 0, 0.5).svg_value()
        '#ff0000'
        """
        text = self.name if self.name and self.a == 1.0 else self.opaque.hex
        return f"{text} {self.icc}" if self.icc else text

    def __str__(self) -> str:
        return self.svg_value()
