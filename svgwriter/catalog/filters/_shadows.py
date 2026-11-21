"""
Blurs, glows and shadows.
"""

from __future__ import annotations

import math
from typing import Any

from ..._internal._typing import Opacity
from ...model.color.color import Color
from ...model.elements import (
    CompositeOperator,
    FeComposite,
    FeGaussianBlur,
    FeMerge,
    FeOffset,
    Filter,
    StandardInput,
)
from ...model.elements.core import Element
from ..preset import filter
from ._constants import (
    DEFAULT_BLUR,
    DEFAULT_OFFSET,
    FALLBACK_SHADOW,
    LONG_SHADOW_EXTENT,
    LONG_SHADOW_LENGTH,
    SHADOW_ROLE,
    WIDE_EXTENT,
    WIDE_MARGIN,
)
from ._parts import flood, region

__all__ = ["blur", "drop_shadow", "glow", "inner_shadow", "long_shadow"]


@filter
def blur(radius: float | tuple[float, float] = DEFAULT_BLUR, **kwargs: Any) -> Filter:
    """A Gaussian blur; a pair ``(x, y)`` blurs along one axis more than the other, as in motion blur.

    Parameters
    ----------
    radius : float or (float, float), optional
        Standard deviation, in user units. Defaults to 2.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The filter; ``element.filter = svg.filters.blur()`` puts it into ``<defs>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.blur((6, 0)).children[0].get("stdDeviation")
    (6, 0)
    """
    return region(FeGaussianBlur(radius), **kwargs)


@filter
def glow(radius: float = DEFAULT_BLUR, *, color: Color | str | None = None, opacity: Opacity = 1.0,
         **kwargs: Any) -> Filter:
    """A soft halo under the element, in its own colors or in *color*.

    Parameters
    ----------
    radius : float, optional
        Standard deviation of the halo. Defaults to 2.
    color : Color or str, optional
        Halo color. Defaults to None, which blurs the element's own colors.
    opacity : float, optional
        Halo opacity when `color` is given. Defaults to 1.
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The glow filter.

    See Also
    --------
    drop_shadow : An offset, tinted shadow.

    Examples
    --------
    >>> import svgwriter as svg
    >>> [child.tag for child in svg.filters.glow(3).children]
    ['feGaussianBlur', 'feMerge']
    >>> [child.tag for child in svg.filters.glow(3, color="gold").children]
    ['feGaussianBlur', 'feFlood', 'feComposite', 'feMerge']
    """
    kwargs.setdefault("margin", WIDE_MARGIN)
    kwargs.setdefault("extent", WIDE_EXTENT)
    if color is None:
        halo = FeGaussianBlur(radius, in_=StandardInput.SOURCE_GRAPHIC)
        return region(halo, FeMerge(halo, StandardInput.SOURCE_GRAPHIC), **kwargs)
    blurred = FeGaussianBlur(radius, in_=StandardInput.SOURCE_ALPHA)
    tint = flood(color, opacity, None, str(color))
    halo = FeComposite(CompositeOperator.IN, in_=tint, in2=blurred)
    return region(blurred, tint, halo, FeMerge(halo, StandardInput.SOURCE_GRAPHIC), **kwargs)


@filter
def drop_shadow(dx: float = DEFAULT_OFFSET, dy: float = DEFAULT_OFFSET, blur: float = DEFAULT_BLUR,
                color: Color | str | None = None, opacity: Opacity = 1.0, *, role: str | None = SHADOW_ROLE,
                **kwargs: Any) -> Filter:
    """A blurred, offset, tinted copy of the element's shape, under the element.

    Parameters
    ----------
    dx, dy : float, optional
        Shadow offset. Defaults to 2.
    blur : float, optional
        Standard deviation of the blur. Defaults to 2.
    color : Color or str, optional
        Shadow color. Defaults to None, which takes the theme `role`.
    opacity : float, optional
        Shadow opacity, on top of the color's own alpha. Defaults to 1.
    role : str or None, optional
        Theme role giving the ``flood-color`` when no `color` is given. Defaults to ``"filter.shadow"`` (the
        palette's translucent shadow color).
    **kwargs
        Forwarded to :class:`~svgwriter.Filter`.

    Returns
    -------
    Filter
        The shadow filter.

    See Also
    --------
    inner_shadow : A shadow inside the shape.
    long_shadow : A hard shadow stretched along a direction.

    Examples
    --------
    >>> import svgwriter as svg
    >>> shadow = svg.filters.drop_shadow(3, 3, 1, "navy", 0.4)
    >>> [child.tag for child in shadow.children]
    ['feGaussianBlur', 'feOffset', 'feFlood', 'feComposite', 'feMerge']
    """
    blurred = FeGaussianBlur(blur, in_=StandardInput.SOURCE_ALPHA)
    offset = FeOffset(dx, dy, in_=blurred)
    tint = flood(color, opacity, role, FALLBACK_SHADOW)
    shadow = FeComposite(CompositeOperator.IN, in_=tint, in2=offset)
    return region(blurred, offset, tint, shadow, FeMerge(shadow, StandardInput.SOURCE_GRAPHIC), **kwargs)


@filter
def inner_shadow(dx: float = DEFAULT_OFFSET, dy: float = DEFAULT_OFFSET, blur: float = DEFAULT_BLUR,
                 color: Color | str | None = None, opacity: Opacity = 1.0, *, role: str | None = SHADOW_ROLE,
                 **kwargs: Any) -> Filter:
    """A shadow cast inside the shape, as if it were pressed in.

    Parameters
    ----------
    dx, dy, blur, color, opacity, role, **kwargs
        As for :func:`drop_shadow`.

    Returns
    -------
    Filter
        The inner-shadow filter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.filters.inner_shadow().children[2].get("operator")
    <CompositeOperator.OUT: 'out'>
    """
    blurred = FeGaussianBlur(blur, in_=StandardInput.SOURCE_ALPHA)
    offset = FeOffset(dx, dy, in_=blurred)
    rim = FeComposite(CompositeOperator.OUT, in_=StandardInput.SOURCE_ALPHA, in2=offset)
    tint = flood(color, opacity, role, FALLBACK_SHADOW)
    shadow = FeComposite(CompositeOperator.IN, in_=tint, in2=rim)
    return region(blurred, offset, rim, tint, shadow, FeMerge(StandardInput.SOURCE_GRAPHIC, shadow), **kwargs)


@filter
def long_shadow(angle: float = 45.0, length: float = LONG_SHADOW_LENGTH, color: Color | str | None = None,
                opacity: Opacity = 1.0, *, role: str | None = SHADOW_ROLE, **kwargs: Any) -> Filter:
    """A hard shadow stretched *length* units along *angle*, the flat-design long shadow.

    The shape is swept by doubling offsets, so the filter has a handful of primitives for any length.

    Parameters
    ----------
    angle : float, optional
        Direction of the shadow in degrees, clockwise from the x axis (y points down). Defaults to 45.
    length : float, optional
        Length of the shadow in user units. Defaults to 24.
    color, opacity, role, **kwargs
        As for :func:`drop_shadow`.

    Returns
    -------
    Filter
        The long-shadow filter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> sum(child.tag == "feOffset" for child in svg.filters.long_shadow(length=15).children)
    4
    """
    kwargs.setdefault("margin", WIDE_MARGIN)
    kwargs.setdefault("extent", LONG_SHADOW_EXTENT)
    ux, uy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    primitives: list[Element] = []
    swept: Element | StandardInput = StandardInput.SOURCE_ALPHA
    covered = 0.0
    while covered < length:
        step = min(covered + 1, length - covered)
        shifted = FeOffset(ux * step, uy * step, in_=swept)
        swept = FeMerge(swept, shifted)
        primitives += [shifted, swept]
        covered += step
    tint = flood(color, opacity, role, FALLBACK_SHADOW)
    shadow = FeComposite(CompositeOperator.IN, in_=tint, in2=swept)
    return region(*primitives, tint, shadow, FeMerge(shadow, StandardInput.SOURCE_GRAPHIC), **kwargs)
