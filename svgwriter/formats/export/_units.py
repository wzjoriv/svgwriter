"""
Pixels per inch for vector pages: how big a user unit prints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._constants import PX_PER_INCH
from ...model.units.length import Length
from ._constants import PHYSICAL_UNITS

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["dpi_scale", "unit_scale"]


def unit_scale(document: Document, units_per_inch: float = PX_PER_INCH) -> float:
    """How many CSS pixels (1/96 inch) one user unit of *document* prints as.

    Parameters
    ----------
    document : Document
        The page.
    units_per_inch : float, optional
        User units per inch for a document sized in pixels or plain numbers: 96 is CSS, 72 makes
        one unit one point. Defaults to 96.

    Returns
    -------
    float
        ``96 / units_per_inch``, or 1 when the width or height is in ``mm``, ``cm``, ``in``, ``pt``
        or ``pc``, since those already fix the printed size.

    Raises
    ------
    ValueError
        If `units_per_inch` is not above 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._units import unit_scale
    >>> unit_scale(svg.Document(100, 50), 72)
    1.3333333333333333
    >>> unit_scale(svg.Document(210 * svg.mm, 297 * svg.mm), 72)
    1.0
    """
    if units_per_inch <= 0:
        raise ValueError(f"units_per_inch must be above 0, got {units_per_inch}")
    for name in ("width", "height"):
        value = document.root.get(name)
        if value is not None and Length.parse(value).unit in PHYSICAL_UNITS:
            return 1.0
    return PX_PER_INCH / units_per_inch


def dpi_scale(document: Document, dpi: float, units_per_inch: float = PX_PER_INCH) -> float:
    """Pixels per user unit that give *dpi* pixels per printed inch of *document*.

    Parameters
    ----------
    document : Document
        The page.
    dpi : float
        Output pixels per inch.
    units_per_inch : float, optional
        User units per inch of a page sized in pixels or plain numbers, as for :func:`unit_scale`.
        Defaults to 96.

    Returns
    -------
    float
        The raster scale.

    Raises
    ------
    ValueError
        If `units_per_inch` is not above 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._units import dpi_scale
    >>> round(dpi_scale(svg.Document(100, 50), 300, 72), 6)
    4.166667
    >>> dpi_scale(svg.Document(svg.inch(2), svg.inch(1)), 300, 72)
    3.125
    """
    return dpi / PX_PER_INCH * unit_scale(document, units_per_inch)

