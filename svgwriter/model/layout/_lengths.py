"""
Lengths of layout groups: unit resolution against the document scale, padding edges and gaps.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias

from ..._internal._constants import PAGE_LENGTH_DIGITS
from ..._internal._page import page_unit
from ..elements.core import Element
from ..units.lengths import Length, Unit

__all__ = ["Edges", "LayoutLength", "PaddingLike", "edges", "pair", "resolve", "user_scale"]

LayoutLength: TypeAlias = float | str | Length
PaddingLike: TypeAlias = LayoutLength | Sequence[LayoutLength]


def user_scale(element: Element) -> float:
    """User units per CSS pixel in the document holding *element*.

    A root sized ``148mm`` with a 148-wide ``viewBox`` counts user units in millimetres, so a
    layout length of ``2mm`` there is 2 user units; anywhere else lengths convert as CSS pixels.

    Parameters
    ----------
    element : Element
        Any element; its root is inspected.

    Returns
    -------
    float
        The factor from CSS pixels to user units (1 without a sized, viewBoxed root).

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.layout._lengths import user_scale
    >>> doc = svg.Document(size="a6-landscape")
    >>> round(user_scale(doc.root) * svg.mm(1).to_user_units(), 9)
    1.0
    >>> user_scale(svg.group())
    1.0
    """
    unit = page_unit(element)
    return 1.0 if unit is None else unit[1] / Length(1, unit[0]).to_user_units()

def resolve(value: LayoutLength, scale: float = 1.0) -> float:
    """*value* in user units: numbers as given, lengths with units through *scale*.

    Parameters
    ----------
    value : float, str or Length
        A number of user units or a length such as ``"2mm"`` or ``svg.mm(2)``.
    scale : float, optional
        User units per CSS pixel (see :func:`user_scale`). Defaults to 1.0.

    Returns
    -------
    float
        The length in user units.

    Raises
    ------
    ValueError
        For a percentage, which has nothing to refer to in a layout.

    Examples
    --------
    >>> from svgwriter.model.layout._lengths import resolve
    >>> resolve(4), resolve("1in")
    (4.0, 96.0)
    """
    length = Length.parse(value)
    if length.unit is Unit.NONE:
        return length.value
    if length.unit is Unit.PERCENT:
        raise ValueError(f"layout lengths cannot be percentages, got {length}")
    return round(length.to_user_units() * scale, PAGE_LENGTH_DIGITS)


def pair(value: LayoutLength | Sequence[LayoutLength], scale: float = 1.0) -> tuple[float, float]:
    """A length or an ``(x, y)`` pair of lengths as two user-unit numbers.

    Parameters
    ----------
    value : length or (length, length)
        One length for both directions, or the horizontal and vertical lengths.
    scale : float, optional
        User units per CSS pixel. Defaults to 1.0.

    Returns
    -------
    (float, float)
        The horizontal and vertical lengths.

    Raises
    ------
    ValueError
        If a sequence does not hold exactly two lengths.

    Examples
    --------
    >>> from svgwriter.model.layout._lengths import pair
    >>> pair(3), pair((4, "1in"))
    ((3.0, 3.0), (4.0, 96.0))
    """
    if isinstance(value, (str, Length)) or not isinstance(value, Sequence):
        single = resolve(value, scale)
        return single, single
    if len(value) != 2:
        raise ValueError(f"a gap is one length or an (x, y) pair, not {len(value)} values")
    return resolve(value[0], scale), resolve(value[1], scale)


@dataclass(frozen=True)
class Edges:
    """Space on the four sides of a box, in user units.

    Attributes
    ----------
    top, right, bottom, left : float
        The four sides, in CSS order.

    Examples
    --------
    >>> from svgwriter.model.layout._lengths import Edges
    >>> Edges(1, 2, 3, 4).horizontal, Edges(1, 2, 3, 4).vertical
    (6.0, 4.0)
    """

    top: float
    right: float
    bottom: float
    left: float

    @property
    def horizontal(self) -> float:
        """Left plus right."""
        return float(self.left + self.right)

    @property
    def vertical(self) -> float:
        """Top plus bottom."""
        return float(self.top + self.bottom)


def edges(value: PaddingLike, scale: float = 1.0) -> Edges:
    """Padding as :class:`Edges`, written like CSS ``padding``.

    Parameters
    ----------
    value : length or sequence of lengths
        One length for every side, ``(vertical, horizontal)``, or ``(top, right, bottom, left)``.
    scale : float, optional
        User units per CSS pixel. Defaults to 1.0.

    Returns
    -------
    Edges
        The four sides in user units.

    Raises
    ------
    ValueError
        If a sequence holds other than two or four lengths.

    Examples
    --------
    >>> from svgwriter.model.layout._lengths import edges
    >>> edges(2)
    Edges(top=2.0, right=2.0, bottom=2.0, left=2.0)
    >>> edges((1, 3))
    Edges(top=1.0, right=3.0, bottom=1.0, left=3.0)
    >>> edges((1, 2, 3, 4))
    Edges(top=1.0, right=2.0, bottom=3.0, left=4.0)
    """
    if isinstance(value, (str, Length)) or not isinstance(value, Sequence):
        side = resolve(value, scale)
        return Edges(side, side, side, side)
    sides = [resolve(part, scale) for part in value]
    if len(sides) == 2:
        return Edges(sides[0], sides[1], sides[0], sides[1])
    if len(sides) == 4:
        return Edges(*sides)
    raise ValueError(f"padding is one length, (vertical, horizontal) or (top, right, bottom, left), "
                     f"not {len(sides)} values")
