"""
Color adjustments and contrast: saturation, hue, grey, inversion and WCAG contrast.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._internal._typing import Opacity
from ._constants import CONTRAST_OFFSET, DARK_LUMINANCE, DEGREES
from ._spaces import oklab_to_srgb

if TYPE_CHECKING:
    from .color import Color, ColorLike

__all__ = ["ColorAdjustments"]

HALF_TURN = DEGREES / 2


class ColorAdjustments:
    """Saturation, hue and contrast helpers shared by :class:`~svgwriter.color.Color`."""

    def saturate(self, amount: Opacity) -> Color:
        """Raise HSL saturation by an amount.

        Parameters
        ----------
        amount : float
            Change in saturation on a ``0..1`` scale; negative desaturates. The result is clamped.

        Returns
        -------
        Color
            The adjusted color, with the same hue, lightness and alpha.

        See Also
        --------
        desaturate : Lower saturation instead.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#806060").saturate(0.5).hex
        '#b82828'
        """
        from .color import Color

        hue, saturation, lightness = self.hsl  # type: ignore[attr-defined]
        return Color.from_hsl(hue, min(max(saturation + amount, 0.0), 1.0), lightness, self.a)  # type: ignore[attr-defined]

    def desaturate(self, amount: Opacity) -> Color:
        """Lower HSL saturation by an amount.

        Parameters
        ----------
        amount : float
            Decrease in saturation on a ``0..1`` scale.

        Returns
        -------
        Color
            The adjusted color.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").desaturate(1).hex
        '#808080'
        """
        return self.saturate(-amount)

    def hue_shift(self, degrees: float) -> Color:
        """Turn the HSL hue.

        Parameters
        ----------
        degrees : float
            Angle to add to the hue; any value, taken modulo 360.

        Returns
        -------
        Color
            The color with the same saturation, lightness and alpha.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("red").hue_shift(120).hex
        '#00ff00'
        """
        from .color import Color

        hue, saturation, lightness = self.hsl  # type: ignore[attr-defined]
        return Color.from_hsl((hue + degrees) % DEGREES, saturation, lightness, self.a)  # type: ignore[attr-defined]

    def complement(self) -> Color:
        """The color with its hue turned half way round.

        Returns
        -------
        Color
            The complementary color.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("blue").complement().hex
        '#ffff00'
        """
        return self.hue_shift(HALF_TURN)

    def grayscale(self) -> Color:
        """The grey of the same perceived lightness (OKLab lightness of the exact color, no chroma).

        Returns
        -------
        Color
            A neutral grey with the same alpha.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("yellow").grayscale().hex
        '#f4f4f4'
        """
        from .color import Color

        lightness, _, _ = self.coords("oklab")  # type: ignore[attr-defined]
        r, g, b = (min(max(c, 0.0), 1.0) for c in oklab_to_srgb((lightness, 0.0, 0.0)))
        return Color(r, g, b, self.a)  # type: ignore[attr-defined]

    def invert(self) -> Color:
        """The negative: every channel ``c`` becomes ``1 - c``; alpha is kept.

        Returns
        -------
        Color
            The inverted color.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#ff8000").invert().hex
        '#007fff'
        """
        from .color import Color

        r, g, b = (1.0 - c for c in self.rgb)  # type: ignore[attr-defined]
        return Color(r, g, b, self.a)  # type: ignore[attr-defined]

    def contrast(self, other: ColorLike) -> float:
        """The WCAG 2 contrast ratio with another color, from 1 to 21.

        Parameters
        ----------
        other : Color or str or sequence of float
            The second color; the order does not matter. Alpha is ignored.

        Returns
        -------
        float
            ``(L1 + 0.05) / (L2 + 0.05)`` with ``L1`` the lighter relative luminance. Body text
            needs 4.5 for WCAG AA, large text 3.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> round(Color.parse("black").contrast("white"), 1)
        21.0
        """
        from .color import as_color

        low, high = sorted((self.luminance, as_color(other).luminance))  # type: ignore[attr-defined]
        return (high + CONTRAST_OFFSET) / (low + CONTRAST_OFFSET)

    @property
    def is_dark(self) -> bool:
        """Whether white text reads better on this color than black text.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("navy").is_dark, Color.parse("yellow").is_dark
        (True, False)
        """
        return bool(self.luminance < DARK_LUMINANCE)  # type: ignore[attr-defined]

    @property
    def is_light(self) -> bool:
        """Whether black text reads better on this color than white text; the opposite of :attr:`is_dark`.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("white").is_light
        True
        """
        return not self.is_dark

    def readable(self, first: ColorLike = "black", second: ColorLike = "white") -> Color:
        """Of two colors, the one with more contrast on this color, for text on it.

        Parameters
        ----------
        first, second : Color or str or sequence of float, optional
            The candidates. Default to black and white.

        Returns
        -------
        Color
            `first` or `second`, whichever has the higher :meth:`contrast`; `first` on a tie.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> Color.parse("#0f766e").readable().hex
        '#ffffff'
        >>> Color.parse("#fbbf24").readable("#1f2933", "#ffffff").hex
        '#1f2933'
        """
        from .color import as_color

        first, second = as_color(first), as_color(second)
        return second if self.contrast(second) > self.contrast(first) else first
