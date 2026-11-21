"""
Edge filters: outline, emboss and goo.
"""

from __future__ import annotations

from typing import Any

from .._internal._typing import Opacity
from ..color.color import Color
from ..elements import (
    ColorMatrixType,
    CompositeOperator,
    FeColorMatrix,
    FeComposite,
    FeConvolveMatrix,
    FeGaussianBlur,
    FeMerge,
    FeMorphology,
    Filter,
    MorphologyOperator,
    StandardInput,
)
from ..preset import filter
from ._constants import (
    EMBOSS_KERNEL,
    FALLBACK_INK,
    GOO_BLUR,
    GOO_CONTRAST,
    GOO_CUTOFF,
    INK_ROLE,
    OUTLINE_WIDTH,
    WIDE_EXTENT,
    WIDE_MARGIN,
)
from ._parts import flood, region

__all__ = ["emboss", "goo", "outline"]


@filter
def outline(width: float = OUTLINE_WIDTH, color: Color | str | None = None, opacity: Opacity = 1.0, *,
            role: str | None = INK_ROLE, **kwargs: Any) -> Filter:
    """A solid ring *width* units wide around the shape, grown from its alpha; text stays text.

    Parameters
    ----------
    width : float, optional
        Ring width. Defaults to 2.
    color : Color or str, optional
        Ring color. Defaults to None, which takes the theme `role`.
    opacity : float, optional
        Ring opacity. Defaults to 1.
    role : str or None, optional
        Theme role giving the ``flood-color`` when no `color` is given. Defaults to ``"filter.ink"`` (the
        palette's foreground).
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The outline filter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.outline(3, "white").children[0].get("operator")
    <MorphologyOperator.DILATE: 'dilate'>
    """
    grown = FeMorphology(MorphologyOperator.DILATE, width, in_=StandardInput.SOURCE_ALPHA)
    tint = flood(color, opacity, role, FALLBACK_INK)
    ring = FeComposite(CompositeOperator.IN, in_=tint, in2=grown)
    return region(grown, tint, ring, FeMerge(ring, StandardInput.SOURCE_GRAPHIC), **kwargs)


@filter
def emboss(strength: float = 1.0, **kwargs: Any) -> Filter:
    """A stamped-relief look: edges facing the light brighten, the others darken.

    Parameters
    ----------
    strength : float, optional
        Scale of the relief kernel; 0 leaves the element unchanged. Defaults to 1.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The emboss filter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.emboss().children[0].tag
    'feConvolveMatrix'
    """
    centre = len(EMBOSS_KERNEL) // 2
    kernel = [value * strength if index != centre else 1.0 for index, value in enumerate(EMBOSS_KERNEL)]
    return region(FeConvolveMatrix(kernel, 3, divisor=1, preserve_alpha=True), **kwargs)


@filter
def goo(blur: float = GOO_BLUR, *, crisp: bool = True, **kwargs: Any) -> Filter:
    """Metaballs: shapes that come close melt into each other. Apply it to a group of shapes.

    The group is blurred, then its alpha is thresholded back to a sharp edge, so the blurred overlaps
    become bridges.

    Parameters
    ----------
    blur : float, optional
        How far apart shapes still merge, as a blur deviation. Defaults to 8.
    crisp : bool, optional
        Draw the shapes' own colors on top of the merged body. Defaults to True.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The goo filter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> blobs = svg.group(svg.circle(10, 10, 8), svg.circle(24, 10, 8))
    >>> blobs.filter = svg.filters.goo(6)
    >>> [child.tag for child in blobs.get("filter").element]
    ['feGaussianBlur', 'feColorMatrix', 'feComposite']
    """
    kwargs.setdefault("margin", WIDE_MARGIN)
    kwargs.setdefault("extent", WIDE_EXTENT)
    blurred = FeGaussianBlur(blur, in_=StandardInput.SOURCE_GRAPHIC)
    rows = [1.0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 0, GOO_CONTRAST, GOO_CUTOFF]
    body = FeColorMatrix(ColorMatrixType.MATRIX, rows, in_=blurred)
    if not crisp:
        return region(blurred, body, **kwargs)
    return region(blurred, body, FeComposite(CompositeOperator.ATOP, in_=StandardInput.SOURCE_GRAPHIC, in2=body),
                  **kwargs)
