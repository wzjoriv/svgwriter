"""
Straight-edged patterns: stripes, hatch, crosshatch, grid, checker and dots.
"""

from __future__ import annotations

from typing import Any

from ...model.color.color import Color
from ...model.elements import Circle, Pattern, Rect
from ..preset import pattern
from ._constants import DEFAULT_ANGLE, DEFAULT_GAP, DOT_RADIUS, LINE_WIDTH, ROLE
from ._tile import ink, tile

__all__ = ["checker", "crosshatch", "dots", "grid", "hatch", "stripes"]


@pattern
def stripes(*, angle: float = DEFAULT_ANGLE, gap: float = DEFAULT_GAP, width: float | None = None,
            color: Color | str | None = None, role: str | None = ROLE, background: Color | str | None = None,
            **kwargs: Any) -> Pattern:
    """Parallel bands, *width* thick and *gap* apart, turned by *angle* degrees.

    Parameters
    ----------
    angle : float, optional
        Rotation of the bands in degrees; 0 gives vertical bands. Defaults to 45.
    gap : float, optional
        Space between bands, in user units. Defaults to 6.
    width : float, optional
        Thickness of a band. Defaults to None, which equals `gap`.
    color : Color or str, optional
        Band color. Defaults to None, which takes the theme `role`.
    role : str or None, optional
        Theme role of the bands when no `color` is given. Defaults to ``"pattern"`` (the palette's primary
        color); None draws them black.
    background : Color or str, optional
        Fill behind the bands. Defaults to None (transparent).
    **kwargs
        Forwarded to :class:`~svgwriter.Pattern`.

    Returns
    -------
    Pattern
        A paint: ``fill=svg.patterns.stripes()`` puts it into the document's ``<defs>``.

    See Also
    --------
    hatch : Thin lines instead of bands.

    Examples
    --------
    >>> import svgwriter as svg
    >>> bands = svg.patterns.stripes(angle=30, gap=4, color="teal")
    >>> bands.get("width"), bands.get("patternTransform")
    (8, 'rotate(30)')
    """
    thick = gap if width is None else width
    period = thick + gap
    return tile(period, period, [ink(Rect(0, 0, thick, period), color, role)], angle=angle, background=background,
                **kwargs)


@pattern
def hatch(*, angle: float = DEFAULT_ANGLE, gap: float = DEFAULT_GAP, width: float = LINE_WIDTH,
          color: Color | str | None = None, role: str | None = ROLE, background: Color | str | None = None,
          **kwargs: Any) -> Pattern:
    """Thin parallel lines, as in a technical drawing's section fill.

    Parameters
    ----------
    angle : float, optional
        Rotation of the lines in degrees. Defaults to 45.
    gap : float, optional
        Space between lines. Defaults to 6.
    width : float, optional
        Line thickness. Defaults to 1.
    color, role, background, **kwargs
        As for :func:`stripes`.

    Returns
    -------
    Pattern
        The hatch paint.

    See Also
    --------
    crosshatch : Lines in two directions.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.patterns.hatch(gap=3).get("width")
    4.0
    """
    return stripes(angle=angle, gap=gap, width=width, color=color, role=role, background=background, **kwargs)


def _lattice(angle: float, gap: float, width: float, color: Color | str | None, role: str | None,
             background: Color | str | None, kwargs: dict[str, Any]) -> Pattern:
    period = gap + width
    lines = [ink(Rect(0, 0, width, period), color, role), ink(Rect(0, 0, period, width), color, role)]
    return tile(period, period, lines, angle=angle, background=background, **kwargs)


@pattern
def crosshatch(*, angle: float = DEFAULT_ANGLE, gap: float = DEFAULT_GAP, width: float = LINE_WIDTH,
               color: Color | str | None = None, role: str | None = ROLE, background: Color | str | None = None,
               **kwargs: Any) -> Pattern:
    """Thin lines in two perpendicular directions, turned by *angle* degrees.

    Parameters
    ----------
    angle : float, optional
        Rotation in degrees. Defaults to 45.
    gap : float, optional
        Space between lines. Defaults to 6.
    width : float, optional
        Line thickness. Defaults to 1.
    color, role, background, **kwargs
        As for :func:`stripes`.

    Returns
    -------
    Pattern
        The crosshatch paint.

    See Also
    --------
    grid : The same lines along the axes.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.patterns.crosshatch().children)
    2
    """
    return _lattice(angle, gap, width, color, role, background, kwargs)


@pattern
def grid(*, gap: float = 2 * DEFAULT_GAP, width: float = LINE_WIDTH, angle: float = 0.0,
         color: Color | str | None = None, role: str | None = ROLE, background: Color | str | None = None,
         **kwargs: Any) -> Pattern:
    """Graph paper: horizontal and vertical lines *gap* apart.

    Parameters
    ----------
    gap : float, optional
        Cell size between lines. Defaults to 12.
    width : float, optional
        Line thickness. Defaults to 1.
    angle : float, optional
        Rotation in degrees. Defaults to 0.
    color, role, background, **kwargs
        As for :func:`stripes`.

    Returns
    -------
    Pattern
        The grid paint.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.patterns.grid(gap=9).get("height")
    10.0
    """
    return _lattice(angle, gap, width, color, role, background, kwargs)


@pattern
def checker(*, size: float = 2 * DEFAULT_GAP, angle: float = 0.0, color: Color | str | None = None,
            role: str | None = ROLE, background: Color | str | None = None, **kwargs: Any) -> Pattern:
    """A checkerboard of *size* squares.

    Parameters
    ----------
    size : float, optional
        Side of a square. Defaults to 12.
    angle : float, optional
        Rotation in degrees; 45 gives diamonds. Defaults to 0.
    color, role, background, **kwargs
        As for :func:`stripes`; `background` colors the other squares.

    Returns
    -------
    Pattern
        The checker paint.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.patterns.checker(size=5, color="black", background="white").get("width")
    10
    """
    squares = [ink(Rect(0, 0, size, size), color, role), ink(Rect(size, size, size, size), color, role)]
    return tile(2 * size, 2 * size, squares, angle=angle, background=background, **kwargs)


@pattern
def dots(*, gap: float = DEFAULT_GAP, radius: float = DOT_RADIUS, stagger: bool = True, angle: float = 0.0,
         color: Color | str | None = None, role: str | None = ROLE, background: Color | str | None = None,
         **kwargs: Any) -> Pattern:
    """Polka dots of *radius*, *gap* apart, in a staggered or square arrangement.

    Parameters
    ----------
    gap : float, optional
        Space between neighbouring dots in a row. Defaults to 6.
    radius : float, optional
        Dot radius. Defaults to 1.5.
    stagger : bool, optional
        Offset every other row by half a step. Defaults to True.
    angle : float, optional
        Rotation in degrees. Defaults to 0.
    color, role, background, **kwargs
        As for :func:`stripes`.

    Returns
    -------
    Pattern
        The dot paint.

    Examples
    --------
    >>> import svgwriter as svg
    >>> len(svg.patterns.dots().children), len(svg.patterns.dots(stagger=False).children)
    (5, 1)
    """
    period = gap + 2 * radius
    centers = [(period / 2, period / 2)]
    if stagger:
        centers += [(0, 0), (period, 0), (0, period), (period, period)]
    circles = [ink(Circle(x, y, radius), color, role) for x, y in centers]
    return tile(period, period, circles, angle=angle, background=background, **kwargs)
