"""
Ready-made filters and markers, and the ``drawing`` decorator.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, Concatenate

from .._internal._typing import Opacity, P
from ..color.color import Color
from ..document import Document
from ..elements.clip import Marker
from ..elements.filters import (
    CompositeOperator,
    FeComposite,
    FeFlood,
    FeGaussianBlur,
    FeMerge,
    FeOffset,
    Filter,
    StandardInput,
)
from ..elements.shapes import Path
from ..pathdata.builder import PathBuilder
from ._constants import (
    DEFAULT_BLUR,
    DEFAULT_SHADOW_OFFSET,
    DEFAULT_SHADOW_OPACITY,
    FILTER_EXTENT,
    FILTER_MARGIN,
    MARKER_SIZE,
)

__all__ = ["arrow_marker", "drawing", "drop_shadow", "glow"]


def drop_shadow(
    dx: float = DEFAULT_SHADOW_OFFSET,
    dy: float = DEFAULT_SHADOW_OFFSET,
    blur: float = DEFAULT_BLUR,
    color: Color | str = "black",
    opacity: Opacity = DEFAULT_SHADOW_OPACITY,
    **kwargs: Any,
) -> Filter:
    """Build a drop-shadow filter.

    The filter makes a blurred, offset, tinted copy of the source alpha and
    merges it under the source graphic. The filter region is enlarged so the
    shadow is not clipped.

    Parameters
    ----------
    dx, dy : float, optional
        Shadow offset. Defaults to 2.0.
    blur : float, optional
        Gaussian standard deviation. Defaults to 2.0.
    color : Color or str, optional
        Shadow color. Defaults to ``"black"``.
    opacity : float, optional
        Shadow opacity. Defaults to 0.5.
    **kwargs
        Forwarded to :class:`~svgwriter.elements.filters.Filter`.

    Returns
    -------
    Filter
        A filter to add to ``<defs>`` and reference with ``filter="url(#id)"``.

    See Also
    --------
    glow : A soft halo instead of an offset shadow.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.builder import drop_shadow
    >>> shadow = drop_shadow(dx=3, dy=3, blur=1)
    >>> type(shadow).__name__, len(shadow.children)
    ('Filter', 5)
    """
    kwargs.setdefault("x", FILTER_MARGIN)
    kwargs.setdefault("y", FILTER_MARGIN)
    kwargs.setdefault("width", FILTER_EXTENT)
    kwargs.setdefault("height", FILTER_EXTENT)
    blurred = FeGaussianBlur(blur, in_=StandardInput.SOURCE_ALPHA)
    offset = FeOffset(dx, dy, in_=blurred)
    flood = FeFlood(color, opacity)
    tinted = FeComposite(CompositeOperator.IN, in_=flood, in2=offset)
    merge = FeMerge(tinted, StandardInput.SOURCE_GRAPHIC)
    return Filter(blurred, offset, flood, tinted, merge, **kwargs)


def glow(radius: float = DEFAULT_BLUR, **kwargs: Any) -> Filter:
    """Build a soft glow filter in the element's own colors.

    A blurred copy of the source graphic is merged under the source.

    Parameters
    ----------
    radius : float, optional
        Gaussian standard deviation. Defaults to 2.0.
    **kwargs
        Forwarded to :class:`~svgwriter.elements.filters.Filter`.

    Returns
    -------
    Filter
        A filter to add to ``<defs>`` and reference with ``filter="url(#id)"``.

    See Also
    --------
    drop_shadow : An offset, tinted shadow.

    Examples
    --------
    >>> from svgwriter.builder import glow
    >>> [child.tag for child in glow(3).children]
    ['feGaussianBlur', 'feMerge']
    """
    kwargs.setdefault("x", FILTER_MARGIN)
    kwargs.setdefault("y", FILTER_MARGIN)
    kwargs.setdefault("width", FILTER_EXTENT)
    kwargs.setdefault("height", FILTER_EXTENT)
    blurred = FeGaussianBlur(radius, in_=StandardInput.SOURCE_GRAPHIC)
    return Filter(blurred, FeMerge(blurred, StandardInput.SOURCE_GRAPHIC), **kwargs)


def arrow_marker(color: Color | str = "black", size: float = MARKER_SIZE, **kwargs: Any) -> Marker:
    """Build a filled triangular arrowhead for ``marker-end``.

    The marker orients itself along the line it decorates.

    Parameters
    ----------
    color : Color or str, optional
        Fill of the arrowhead. Defaults to ``"black"``.
    size : float, optional
        Width and height of the marker. Defaults to 10.0.
    **kwargs
        Forwarded to :class:`~svgwriter.elements.clip.Marker`.

    Returns
    -------
    Marker
        A marker to add to ``<defs>``.

    See Also
    --------
    svgwriter.builder.arrow : An arrow drawn directly as a path.

    Examples
    --------
    >>> from svgwriter.builder import arrow_marker
    >>> arrow_marker("red", 4).to_string(xml_declaration=False, pretty=False)
    '<marker viewBox="0 0 4 4" refX="4" refY="2" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L4 2 L0 4 Z" fill="red"/></marker>'
    """
    head = PathBuilder().move_to(0, 0).line_to(size, size / 2).line_to(0, size).close()
    kwargs.setdefault("orient", "auto")
    return Marker(
        Path(head, fill=color),
        ref_x=size,
        ref_y=size / 2,
        marker_width=size,
        marker_height=size,
        view_box=(0, 0, size, size),
        **kwargs,
    )


def drawing(width: float, height: float, **root: Any) -> Callable[[Callable[Concatenate[Document, P], object]], Callable[P, Document]]:
    """Turn ``f(doc, *args)`` into ``f(*args) -> Document``.

    The decorated function receives a fresh :class:`~svgwriter.Document` of the
    given size on every call and draws into it; its return value is ignored.

    Parameters
    ----------
    width, height : float
        Size of the document created for each call.
    **root
        Attributes forwarded to the :class:`~svgwriter.Document` constructor.

    Returns
    -------
    callable
        A decorator producing a function that returns the finished document.

    Examples
    --------
    >>> @drawing(10, 10)
    ... def dot(doc, color="red"):
    ...     doc.add(Path("M5 5 h1", stroke=color))
    >>> isinstance(dot(), Document)
    True
    """

    def decorate(func: Callable[Concatenate[Document, P], object]) -> Callable[P, Document]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Document:
            doc = Document(width, height, **root)
            func(doc, *args, **kwargs)
            return doc

        return wrapper

    return decorate
