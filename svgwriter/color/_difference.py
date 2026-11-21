"""
Color difference: Euclidean distance in OKLab and CIEDE2000 in CIE Lab.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ._channels import ColorChannels
from ._constants import (
    DE2000_L_MID,
    DE2000_L_WIDTH,
    DE2000_POW7,
    DE2000_ROTATION_ANGLE,
    DE2000_ROTATION_CENTRE,
    DE2000_ROTATION_WIDTH,
    DE2000_SC,
    DE2000_SH,
    DE2000_SL,
    DE2000_T,
    DEGREES,
)

if TYPE_CHECKING:
    from .color import ColorLike

__all__ = ["ColorDifference", "ciede2000"]

HALF_TURN = DEGREES / 2


def _hue(b: float, a: float) -> float:
    return 0.0 if a == 0 and b == 0 else math.degrees(math.atan2(b, a)) % DEGREES


def ciede2000(first: Sequence[float], second: Sequence[float]) -> float:
    """The CIEDE2000 color difference of two CIE Lab colors, with unit weights.

    Parameters
    ----------
    first, second : sequence of float
        ``(L, a, b)`` with L in ``0..100``.

    Returns
    -------
    float
        ΔE00: about 1 is the smallest difference most observers notice side by side.

    Notes
    -----
    Implements Sharma, Wu and Dalal, "The CIEDE2000 color-difference formula: implementation
    notes, supplementary test data, and mathematical observations" (2005), including its
    conventions for the mean hue and the hue difference when a chroma is zero.

    Examples
    --------
    >>> from svgwriter.color._difference import ciede2000
    >>> round(ciede2000((50, 2.6772, -79.7751), (50, 0, -82.7485)), 4)
    2.0425
    """
    l1, a1, b1 = first
    l2, a2, b2 = second
    mean_c = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = (1 - math.sqrt(mean_c ** 7 / (mean_c ** 7 + DE2000_POW7))) / 2
    a1, a2 = a1 * (1 + g), a2 * (1 + g)
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    h1, h2 = _hue(b1, a1), _hue(b2, a2)
    dh = h2 - h1
    if c1 * c2 == 0:
        dh = 0.0
    elif dh > HALF_TURN:
        dh -= DEGREES
    elif dh < -HALF_TURN:
        dh += DEGREES
    d_hue = 2 * math.sqrt(c1 * c2) * math.sin(math.radians(dh) / 2)
    mean_l, mean_c = (l1 + l2) / 2, (c1 + c2) / 2
    if c1 * c2 == 0:
        mean_h = h1 + h2
    elif abs(h1 - h2) <= HALF_TURN:
        mean_h = (h1 + h2) / 2
    else:
        mean_h = (h1 + h2 + DEGREES) / 2 if h1 + h2 < DEGREES else (h1 + h2 - DEGREES) / 2
    t = 1 + sum(w * math.cos(math.radians(m * mean_h + offset)) for w, m, offset in DE2000_T)
    lightness_offset = (mean_l - DE2000_L_MID) ** 2
    s_l = 1 + DE2000_SL * lightness_offset / math.sqrt(DE2000_L_WIDTH + lightness_offset)
    s_c = 1 + DE2000_SC * mean_c
    s_h = 1 + DE2000_SH * mean_c * t
    rotation = DE2000_ROTATION_ANGLE * math.exp(-(((mean_h - DE2000_ROTATION_CENTRE) / DE2000_ROTATION_WIDTH) ** 2))
    r_t = -2 * math.sqrt(mean_c ** 7 / (mean_c ** 7 + DE2000_POW7)) * math.sin(math.radians(rotation))
    terms = ((l2 - l1) / s_l, (c2 - c1) / s_c, d_hue / s_h)
    return math.sqrt(terms[0] ** 2 + terms[1] ** 2 + terms[2] ** 2 + r_t * terms[1] * terms[2])


class ColorDifference(ColorChannels):
    """Perceptual distances shared by :class:`~svgwriter.color.Color`."""

    def delta(self, other: ColorLike) -> float:
        """The distance to another color in OKLab (ΔE OK).

        Parameters
        ----------
        other : Color or str or sequence of float
            The second color. Alpha is ignored.

        Returns
        -------
        float
            The Euclidean distance between the exact OKLab values: 0 for the same color, about
            0.02 for a just noticeable difference, 1 from black to white.

        See Also
        --------
        delta_e2000 : The CIEDE2000 difference used in print and colour science.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> round(Color.parse("black").delta("white"), 4)
        1.0
        >>> Color.parse("red").delta("#ff0000")
        0.0
        """
        from .color import as_color

        return math.dist(self.coords("oklab"), as_color(other).coords("oklab"))

    def delta_e2000(self, other: ColorLike) -> float:
        """The CIEDE2000 difference to another color (ΔE00), from their CIE Lab values.

        Parameters
        ----------
        other : Color or str or sequence of float
            The second color. Alpha is ignored.

        Returns
        -------
        float
            ΔE00: below 1 is hard to see, 2 to 10 is visible at a glance, and very different
            colors reach 100 and more.

        See Also
        --------
        delta : The simpler OKLab distance.
        ciede2000 : The formula on raw Lab values.

        Notes
        -----
        Lab here is CSS Color 4's (D50 white), so ``lab(...)`` colors are compared exactly.

        Examples
        --------
        >>> from svgwriter.color import Color
        >>> round(Color.parse("lab(50 2.6772 -79.7751)").delta_e2000("lab(50 0 -82.7485)"), 4)
        2.0425
        """
        from .color import as_color

        return ciede2000(self.coords("lab"), as_color(other).coords("lab"))
