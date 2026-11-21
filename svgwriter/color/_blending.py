"""
Color arithmetic: alpha, lightness, mixing and scaling.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from numbers import Real
from typing import TYPE_CHECKING, Literal, TypeAlias

from .._internal._typing import Opacity
from ._constants import DEGREES, MIX_SPACES
from ._spaces import (
    Triple,
    linear_to_srgb,
    oklab_to_oklch,
    oklab_to_srgb,
    oklch_to_oklab,
    srgb_to_linear,
    srgb_to_oklab,
)

if TYPE_CHECKING:
    from .color import Color, ColorLike

__all__ = ["ColorBlending", "MixSpace"]

MixSpace: TypeAlias = Literal["srgb", "linear", "oklab", "oklch"]


def _lerp(start: Sequence[float], end: Sequence[float], weight: float) -> Triple:
    a, b, c = (s + (e - s) * weight for s, e in zip(start, end, strict=True))
    return (a, b, c)


class ColorBlending:
    """Adjustments and operators shared by :class:`~svgwriter.color.Color`."""

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
        >>> from svgwriter.color import Color
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
        space : {"srgb", "linear", "oklab", "oklch"}, optional
            Where to interpolate: the stored sRGB channels, linear-light sRGB (physically even
            blending of light), OKLab (perceptually even steps) or OKLCH (OKLab with hue taken the
            shorter way round, so saturated colors stay saturated). Defaults to ``"srgb"``.

        Returns
        -------
        Color
            The blended color, clipped to the sRGB gamut; alpha is blended linearly.

        Raises
        ------
        ValueError
            If `other` is not a valid color or `space` is unknown.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").mix("blue", 0.25).hex
        '#bf0040'
        >>> Color.parse("red").mix("blue", 0.5, space="oklch").hex
        '#ba00c2'
        """
        from .color import Color, as_color

        other = as_color(other)
        if space not in MIX_SPACES:
            raise ValueError(f"unknown mixing space {space!r}; expected one of {sorted(MIX_SPACES)}")
        alpha = self.a + (other.a - self.a) * weight
        if space == "srgb":
            r, g, b = _lerp(self.rgb, other.rgb, weight)
        elif space == "linear":
            r, g, b = linear_to_srgb(_lerp(srgb_to_linear(self.rgb), srgb_to_linear(other.rgb), weight))
        elif space == "oklab":
            r, g, b = oklab_to_srgb(_lerp(srgb_to_oklab(self.rgb), srgb_to_oklab(other.rgb), weight))
        else:
            start, end = oklab_to_oklch(srgb_to_oklab(self.rgb)), oklab_to_oklch(srgb_to_oklab(other.rgb))
            turn = (end[2] - start[2] + DEGREES / 2) % DEGREES - DEGREES / 2
            lightness, chroma, _ = _lerp(start, end, weight)
            r, g, b = oklab_to_srgb(oklch_to_oklab((lightness, chroma, start[2] + turn * weight)))
        return Color(*(min(max(c, 0.0), 1.0) for c in (r, g, b)), alpha)

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
