"""
The built-in markers: arrow, open_arrow, dot, bar, diamond and square.
"""

from __future__ import annotations

from typing import Any

from .._internal._roles import with_role
from ..color.color import Color
from ..elements import Circle, Marker, Polygon, Rect
from ..elements.core import Element
from ..preset import marker
from ._constants import BAR_WIDTH, BOX, CHEVRON_WIDTH, FALLBACK_INK, MARKER_SIZE, ROLE

__all__ = ["arrow", "bar", "diamond", "dot", "open_arrow", "square"]

MIDDLE = BOX / 2


def _marker(shape: Element, size: float, color: Color | str | None, role: str | None, tip: float,
            kwargs: dict[str, Any]) -> Marker:
    """A marker drawing *shape* (in a ``BOX`` square) *size* stroke widths wide, anchored at ``(tip, middle)``."""
    if color is not None or role is None:
        shape.fill = color if color is not None else FALLBACK_INK
    else:
        with_role(shape, role, (), {"fill": FALLBACK_INK})
    kwargs.setdefault("orient", "auto")
    return Marker(shape, ref_x=tip, ref_y=MIDDLE, marker_width=size, marker_height=size, view_box=(0, 0, BOX, BOX),
                  **kwargs)


@marker
def arrow(size: float = MARKER_SIZE, *, color: Color | str | None = None, role: str | None = ROLE,
          **kwargs: Any) -> Marker:
    """A filled triangular arrowhead whose tip sits on the line's end.

    Every marker is sized in stroke widths, so a thicker line gets a proportionally larger head, and
    turns with the line (``orient="auto"``).

    Parameters
    ----------
    size : float, optional
        Width and height in stroke widths. Defaults to 5.
    color : Color or str, optional
        Fill. Defaults to None, which takes the theme `role`.
    role : str or None, optional
        Theme role when no `color` is given. Defaults to ``"arrow.head"`` (the palette's foreground); None
        draws black.
    **kwargs
        Forwarded to :class:`~svgwriter.Marker`.

    Returns
    -------
    Marker
        The marker; ``marker_end=svg.markers.arrow()`` puts it into ``<defs>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> head = svg.markers.arrow(color="red")
    >>> head.get("orient"), head.get("refX"), head[0].get("fill")
    ('auto', 10.0, 'red')
    """
    return _marker(Polygon([(0, 0), (BOX, MIDDLE), (0, BOX)]), size, color, role, BOX, kwargs)


@marker
def open_arrow(size: float = MARKER_SIZE, *, color: Color | str | None = None, role: str | None = ROLE,
               **kwargs: Any) -> Marker:
    """An open chevron arrowhead (``>``) whose point sits on the line's end.

    Parameters
    ----------
    size, color, role, **kwargs
        As for :func:`arrow`.

    Returns
    -------
    Marker
        The open-arrow marker.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.markers.open_arrow()[0].points)
    6
    """
    chevron = Polygon([(0, 0), (BOX, MIDDLE), (0, BOX), (0, BOX - CHEVRON_WIDTH),
                       (BOX - 2 * CHEVRON_WIDTH, MIDDLE), (0, CHEVRON_WIDTH)])
    return _marker(chevron, size, color, role, BOX, kwargs)


@marker
def dot(size: float = MARKER_SIZE, *, color: Color | str | None = None, role: str | None = ROLE,
        **kwargs: Any) -> Marker:
    """A filled circle centred on the vertex.

    Parameters
    ----------
    size, color, role, **kwargs
        As for :func:`arrow`.

    Returns
    -------
    Marker
        The dot marker.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.markers.dot(3)[0].tag
    'circle'
    """
    return _marker(Circle(MIDDLE, MIDDLE, MIDDLE), size, color, role, MIDDLE, kwargs)


@marker
def bar(size: float = MARKER_SIZE, *, color: Color | str | None = None, role: str | None = ROLE,
        **kwargs: Any) -> Marker:
    """A short bar across the line at the vertex, as on a dimension line.

    Parameters
    ----------
    size, color, role, **kwargs
        As for :func:`arrow`.

    Returns
    -------
    Marker
        The bar marker.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.markers.bar()[0].get("height")
    10.0
    """
    return _marker(Rect(MIDDLE - BAR_WIDTH / 2, 0, BAR_WIDTH, BOX), size, color, role, MIDDLE, kwargs)


@marker
def diamond(size: float = MARKER_SIZE, *, color: Color | str | None = None, role: str | None = ROLE,
            **kwargs: Any) -> Marker:
    """A filled diamond centred on the vertex.

    Parameters
    ----------
    size, color, role, **kwargs
        As for :func:`arrow`.

    Returns
    -------
    Marker
        The diamond marker.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.markers.diamond()[0].points)
    4
    """
    return _marker(Polygon([(MIDDLE, 0), (BOX, MIDDLE), (MIDDLE, BOX), (0, MIDDLE)]), size, color, role, MIDDLE,
                   kwargs)


@marker
def square(size: float = MARKER_SIZE, *, color: Color | str | None = None, role: str | None = ROLE,
           **kwargs: Any) -> Marker:
    """A filled square centred on the vertex.

    Parameters
    ----------
    size, color, role, **kwargs
        As for :func:`arrow`.

    Returns
    -------
    Marker
        The square marker.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.markers.square()[0].tag
    'rect'
    """
    return _marker(Rect(0, 0, BOX, BOX), size, color, role, MIDDLE, kwargs)
