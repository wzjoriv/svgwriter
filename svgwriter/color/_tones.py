"""
Tonal adjustments: tints and shades, posterizing, sepia and gamma.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._internal._typing import Opacity
from ._channels import ColorChannels
from ._constants import IDENTITY, MIN_POSTERIZE_STEPS, SEPIA

if TYPE_CHECKING:
    from .color import Color

__all__ = ["ColorTones"]


class ColorTones(ColorChannels):
    """Tints, shades and tone curves shared by :class:`~svgwriter.color.Color`."""

    def tint(self, amount: Opacity) -> Color:
        """Mix with white in OKLab.

        Parameters
        ----------
        amount : float
            Share of white, from 0 (unchanged) to 1 (white).

        Returns
        -------
        Color
            The lighter color, with the same alpha.

        See Also
        --------
        shade : Mix with black instead.
        mix : Mix with any color in any space.

        Notes
        -----
        White and black sit on OKLab's neutral axis, so the straight line to either keeps the OKLab
        hue exactly while lightness changes in perceptually even steps; mixing in sRGB drifts the
        hue (blue turns purple on the way to white).

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#0f766e").tint(0.5).hex
        '#91b9b4'
        >>> Color.parse("blue").tint(0).hex
        '#0000ff'
        """
        from .color import Color

        return self.mix(Color(1.0, 1.0, 1.0, self.a), amount, space="oklab")  # type: ignore[attr-defined, no-any-return]

    def shade(self, amount: Opacity) -> Color:
        """Mix with black in OKLab.

        Parameters
        ----------
        amount : float
            Share of black, from 0 (unchanged) to 1 (black).

        Returns
        -------
        Color
            The darker color, with the same alpha.

        See Also
        --------
        tint : Mix with white instead; its notes explain the choice of OKLab.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#0f766e").shade(0.5).hex
        '#022926'
        """
        from .color import Color

        return self.mix(Color(0.0, 0.0, 0.0, self.a), amount, space="oklab")  # type: ignore[attr-defined, no-any-return]

    def posterize(self, steps: int) -> Color:
        """Round every sRGB channel to one of `steps` evenly spaced levels.

        Parameters
        ----------
        steps : int
            Levels per channel, at least 2; 2 leaves only 0 and 1.

        Returns
        -------
        Color
            The quantized color; alpha is unchanged.

        Raises
        ------
        ValueError
            If `steps` is below 2.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#5a9ad0").posterize(2).hex
        '#00ffff'
        >>> Color.parse("#5a9ad0").posterize(5).hex
        '#4080bf'
        """
        from .color import Color

        if steps < MIN_POSTERIZE_STEPS:
            raise ValueError(f"posterize needs at least {MIN_POSTERIZE_STEPS} steps, got {steps}")
        top = steps - 1
        return Color(*(round(c * top) / top for c in self.rgb), self.a)

    def sepia(self, amount: Opacity = 1.0) -> Color:
        """Tone the color brown like an old photograph, as the CSS ``sepia()`` filter does.

        Parameters
        ----------
        amount : float, optional
            Strength from 0 (unchanged) to 1 (full sepia). Defaults to 1.0.

        Returns
        -------
        Color
            The toned sRGB color, clipped to the gamut; alpha is unchanged.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#3366cc").sepia().hex
        '#897a5f'
        >>> Color.parse("#3366cc").sepia(0).hex
        '#3366cc'
        """
        from .color import Color

        rows = [[i + (s - i) * amount for i, s in zip(ident, sep, strict=True)]
                for ident, sep in zip(IDENTITY, SEPIA, strict=True)]
        return Color(*(min(max(sum(m * c for m, c in zip(row, self.rgb, strict=True)), 0.0), 1.0)
                       for row in rows), self.a)

    def gamma(self, exponent: float) -> Color:
        """Raise every sRGB channel to a power, as an SVG ``feFuncX type="gamma"`` does.

        Parameters
        ----------
        exponent : float
            The power, above 0: above 1 darkens the mid-tones, below 1 lightens them; black and
            white stay put.

        Returns
        -------
        Color
            The adjusted color; alpha is unchanged.

        Raises
        ------
        ValueError
            If `exponent` is not above 0.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color(0.5, 0.5, 0.5).gamma(2).hex
        '#404040'
        >>> Color(0.25, 0.25, 0.25).gamma(0.5).hex
        '#808080'
        """
        from .color import Color

        if exponent <= 0:
            raise ValueError(f"the gamma exponent must be above 0, got {exponent}")
        return Color(*(c ** exponent for c in self.rgb), self.a)
