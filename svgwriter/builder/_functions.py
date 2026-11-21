"""
Small conveniences: themed presets of the basic shapes.
"""

from __future__ import annotations

from typing import Any

from .._internal._roles import with_role
from ..model.elements.shapes import Circle, Line, Rect
from ._constants import DASH_PATTERN, DOT_RADIUS, FALLBACK_INK

__all__ = ["dashed_line", "dot", "outline"]


def outline(x: float, y: float, width: float, height: float, **kwargs: Any) -> Rect:
    """An unfilled rectangle with the theme role ``"outline"``.

    Parameters
    ----------
    x, y : float
        Top-left corner.
    width, height : float
        Size.
    **kwargs
        Forwarded to :class:`~svgwriter.model.elements.Rect`; presentation attributes keep priority over the role.

    Returns
    -------
    Rect
        The rectangle; unfilled and black-stroked when written without a document theme.

    Examples
    --------
    >>> from svgwriter.builder import outline
    >>> str(outline(0, 0, 5, 5))
    '<rect x="0" y="0" width="5" height="5" fill="none" stroke="black" class="role-outline"/>'
    """
    return with_role(Rect(x, y, width, height, **kwargs), "outline", kwargs, {"fill": "none", "stroke": FALLBACK_INK})


def dashed_line(x1: float, y1: float, x2: float, y2: float, **kwargs: Any) -> Line:
    """A dashed line with the theme role ``"line"``.

    Parameters
    ----------
    x1, y1, x2, y2 : float
        End points.
    **kwargs
        Forwarded to :class:`~svgwriter.model.elements.Line`; presentation attributes keep priority over the role.

    Returns
    -------
    Line
        The line, dashed ``4 2``; black when written without a document theme.

    Examples
    --------
    >>> from svgwriter.builder import dashed_line
    >>> line = dashed_line(0, 0, 10, 0, stroke="red")
    >>> line.style["stroke"], line.get("stroke-dasharray")
    ('red', (4, 2))
    """
    line = with_role(Line(x1, y1, x2, y2, **kwargs), "line", kwargs, {"stroke": FALLBACK_INK})
    if "stroke-dasharray" not in line.style:
        line.update(stroke_dasharray=DASH_PATTERN)
    return line


def dot(cx: float, cy: float, r: float = DOT_RADIUS, **kwargs: Any) -> Circle:
    """A small filled circle with the theme role ``"dot"``.

    Parameters
    ----------
    cx, cy : float
        Center.
    r : float, optional
        Radius. Defaults to 2.
    **kwargs
        Forwarded to :class:`~svgwriter.model.elements.Circle`; presentation attributes keep priority over the role.

    Returns
    -------
    Circle
        The circle.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10, theme="dark")
    >>> doc += svg.builder.dot(5, 5)
    >>> ".role-dot { fill:#b45309" in doc.to_string()
    True
    """
    return with_role(Circle(cx, cy, r, **kwargs), "dot", kwargs)
