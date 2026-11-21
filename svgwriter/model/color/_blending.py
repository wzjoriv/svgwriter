"""
Color arithmetic: alpha, lightness, mixing and scaling.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from numbers import Real
from typing import TYPE_CHECKING, Literal, TypeAlias

from ..._internal._typing import Opacity
from ._channels import ColorChannels
from ._constants import DEGREES, MIX_SPACES, POLAR_SPACES
from ._spaces import Triple, convert

if TYPE_CHECKING:
    from .color import Color, ColorLike

__all__ = ["ColorBlending", "MixSpace"]

MixSpace: TypeAlias = Literal["srgb", "linear", "display-p3", "lab", "lch", "oklab", "oklch", "xyz"]


def _lerp(start: Sequence[float], end: Sequence[float], weight: float) -> Triple:
    a, b, c = (s + (e - s) * weight for s, e in zip(start, end, strict=True))
    return (a, b, c)


class ColorBlending(ColorChannels):
    """Adjustments and operators shared by :class:`~svgwriter.model.color.Color`."""

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
        >>> from svgwriter.model.color import Color
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
        >>> from svgwriter.model.color import Color
        >>> Color(0.5, 0.5, 0.5).lighten(0.2).hex
        '#b2b2b2'
        """
        from .color import Color, clamp

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
        >>> from svgwriter.model.color import Color
        >>> Color(0.5, 0.5, 0.5).darken(0.2).hex
        '#4c4c4c'
        """
        return self.lighten(-amount)

    def mix(self, other: ColorLike, weight: Opacity = 0.5, space: MixSpace = "srgb") -> Color:
        """Blend with another color in a chosen space.

        Parameters
        ----------
        other : Color or str or sequence of float
            The color to mix in.
        weight : float, optional
            Share of `other` in the result, from 0 to 1. Defaults to 0.5.
        space : {"srgb", "linear", "display-p3", "lab", "lch", "oklab", "oklch", "xyz"}, optional
            Where to interpolate: sRGB channels, linear-light sRGB (physically even blending of
            light), Display P3, CIE Lab or LCH, OKLab (perceptually even steps), OKLCH (OKLab with
            hue taken the shorter way round, so saturated colors stay saturated) or CIE XYZ (D65).
            Defaults to ``"srgb"``.

        Returns
        -------
        Color
            The blended color; alpha is blended linearly. When either color carries a
            :attr:`source` (a wide-gamut or non-sRGB color), both are mixed from their exact values
            and the result keeps the mixed values in `space`, so nothing is clipped until output.

        Raises
        ------
        ValueError
            If `other` is not a valid color or `space` is unknown.

        Examples
        --------
        >>> from svgwriter.model.color import Color
        >>> Color.parse("red").mix("blue", 0.25).hex
        '#bf0040'
        >>> Color.parse("red").mix("blue", 0.5, space="oklch").hex
        '#ba00c2'
        >>> p3 = Color.parse("color(display-p3 0 1 0)").mix("white", 0.5, space="display-p3")
        >>> p3.to_css("display-p3")
        'color(display-p3 0.5 1 0.5)'
        """
        from .color import Color, as_color

        other = as_color(other)
        if space not in MIX_SPACES:
            raise ValueError(f"unknown mixing space {space!r}; expected one of {sorted(MIX_SPACES)}")
        target = MIX_SPACES[space]
        alpha = self.a + (other.a - self.a) * weight
        start, end = self.coords(target), other.coords(target)
        if target in POLAR_SPACES:
            turn = (end[2] - start[2] + DEGREES / 2) % DEGREES - DEGREES / 2
            lightness, chroma, _ = _lerp(start, end, weight)
            mixed: Triple = (lightness, chroma, start[2] + turn * weight)
        else:
            mixed = _lerp(start, end, weight)
        if self.source is None and other.source is None:
            return Color(*(min(max(c, 0.0), 1.0) for c in convert(mixed, target, "srgb")), alpha)
        return Color.from_space(target, mixed, alpha)

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
        >>> from svgwriter.model.color import Color
        >>> Color(0.5, 0.2, 0.1).scale(2).hex
        '#ff6633'
        """
        from .color import Color, clamp

        return Color(*(clamp(c * factor, 0.0, 1.0) for c in self.rgb), self.a)

    def __add__(self, other: ColorLike) -> Color:
        """Mix evenly with another color (``color + other``)."""
        try:
            return self.mix(other)
        except (TypeError, ValueError):
            return NotImplemented

    def __radd__(self, other: ColorLike) -> Color:
        from .color import as_color

        try:
            return as_color(other).mix(self)
        except (TypeError, ValueError):
            return NotImplemented

    def __mul__(self, factor: float | Color) -> Color:
        """Scale by a number, or multiply channel-wise by another color."""
        from .color import Color

        if isinstance(factor, Color):
            return Color(*(a * b for a, b in zip(self.rgba, factor.rgba, strict=True)))
        if isinstance(factor, Real):
            return self.scale(float(factor))
        return NotImplemented

    def __rmul__(self, factor: float) -> Color:
        return self.scale(float(factor)) if isinstance(factor, Real) else NotImplemented

    def __truediv__(self, divisor: float) -> Color:
        return self.scale(1.0 / divisor) if isinstance(divisor, Real) else NotImplemented
