"""
Pixels per inch for vector pages: how big a user unit prints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._constants import PX_PER_INCH
from ...attributes.length import Length
from ._constants import PHYSICAL_UNITS

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["unit_scale"]


def unit_scale(document: Document, px_per_inch: float = PX_PER_INCH) -> float:
    """How many CSS pixels (1/96 inch) one user unit of *document* prints as.

    Parameters
    ----------
    document : Document
        The page.
    px_per_inch : float, optional
        User units per inch for a document sized in pixels or plain numbers: 96 is CSS, 72 makes
        one unit one point. Defaults to 96.

    Returns
    -------
    float
        ``96 / px_per_inch``, or 1 when the width or height is in ``mm``, ``cm``, ``in``, ``pt``
        or ``pc``, since those already fix the printed size.

    Raises
    ------
    ValueError
        If `px_per_inch` is not above 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._vector._units import unit_scale
    >>> unit_scale(svg.Document(100, 50), 72)
    1.3333333333333333
    >>> unit_scale(svg.Document(210 * svg.mm, 297 * svg.mm), 72)
    1.0
    """
    if px_per_inch <= 0:
        raise ValueError(f"px_per_inch must be above 0, got {px_per_inch}")
    for name in ("width", "height"):
        value = document.root.get(name)
        if value is not None and Length.parse(value).unit in PHYSICAL_UNITS:
            return 1.0
    return PX_PER_INCH / px_per_inch

