"""
Composite shapes registered by name for the CLI and plugins.
"""

from __future__ import annotations

import math
from typing import Any, TypeVar

from ...model.elements.core import Element
from ...model.elements.shapes import Path, Polygon
from ...model.pathdata.builder import PathBuilder
from ..preset import shape
from ._constants import (
    ARROW_HEAD_ANGLE,
    DEFAULT_HEAD_SIZE,
    DEFAULT_INNER_RATIO,
    DEFAULT_STAR_POINTS,
    DEFAULT_TEETH,
    FULL_TURN,
    MIN_SIDES,
    QUARTER_TURN,
    TOOTH_DEPTH_RATIO,
)
from ._rounded import rounded_outline

__all__ = ["arrow", "gear", "regular_polygon", "star"]

E = TypeVar("E", bound=Element)

def _ring(cx: float, cy: float, radii: list[float], rotation: float) -> list[tuple[float, float]]:
    count = len(radii)
    points = []
    for index, radius in enumerate(radii):
        angle = math.radians(rotation + FULL_TURN * index / count)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def _inkscape_star(cx: float, cy: float, outer: float, inner: float, sides: int, angle: float, corner_radius: float,
                   *, flatsided: bool, **kwargs: Any) -> Path:
    from ...formats.inkscape import Star

    if corner_radius > 0:
        raise ValueError("corner_radius= does not apply to Inkscape stars; round them in Inkscape instead")
    return Star.create(cx, cy, outer, inner, sides, angle=angle, flatsided=flatsided, **kwargs)


@shape
def star(
    cx: float,
    cy: float,
    outer: float,
    inner: float | None = None,
    points: int = DEFAULT_STAR_POINTS,
    *,
    corner_radius: float = 0,
    inkscape: bool = False,
    **kwargs: Any,
) -> Polygon | Path:
    """Build a star with *points* tips, pointing up.

    Parameters
    ----------
    cx, cy : float
        Center.
    outer : float
        Radius of the tips.
    inner : float, optional
        Radius of the notches. Defaults to half of `outer`.
    points : int, optional
        Number of tips. Defaults to 5.
    corner_radius : float, optional
        Radius of the circular fillet at every tip and notch; it shrinks where the star is too small
        for it. Defaults to 0 (sharp).
    inkscape : bool, optional
        Build a path carrying Inkscape's star parameters (``sodipodi:type="star"``),
        so the star stays editable with Inkscape's star tool. Defaults to False.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Polygon`
        (:class:`~svgwriter.model.elements.Path` when rounded or `inkscape`).

    Returns
    -------
    Polygon or Path
        The star, a polygon unless `corner_radius` or `inkscape` makes it a path.

    Raises
    ------
    ValueError
        If `inkscape` is combined with `corner_radius`.

    See Also
    --------
    regular_polygon : A polygon without notches.

    Examples
    --------
    >>> from svgwriter.library.paths import star
    >>> len(star(50, 50, 40).points)
    10
    >>> round(star(50, 50, 40, corner_radius=4).bbox.height, 1)
    64.0
    >>> star(50, 50, 40, inkscape=True).get("sodipodi:type")
    'star'
    """
    inner = outer * DEFAULT_INNER_RATIO if inner is None else inner
    if inkscape:
        return _inkscape_star(cx, cy, outer, inner, points, -QUARTER_TURN, corner_radius, flatsided=False, **kwargs)
    vertices = _ring(cx, cy, [outer, inner] * points, -QUARTER_TURN)
    if corner_radius > 0:
        return rounded_outline(vertices, [corner_radius] * len(vertices), **kwargs)
    return Polygon(vertices, **kwargs)


@shape
def gear(cx: float, cy: float, radius: float, teeth: int = DEFAULT_TEETH, **kwargs: Any) -> Polygon:
    """Build a gear outline with square-ish teeth.

    Parameters
    ----------
    cx, cy : float
        Center.
    radius : float
        Radius of the tooth tips.
    teeth : int, optional
        Number of teeth. Defaults to 12.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Polygon`.

    Returns
    -------
    Polygon
        The gear; the tooth root sits 15% of `radius` below the tips.

    See Also
    --------
    star : Another composite polygon.

    Examples
    --------
    >>> from svgwriter.library.paths import gear
    >>> len(gear(0, 0, 20, teeth=8).points)
    32
    """
    depth = radius * TOOTH_DEPTH_RATIO
    radii = [radius, radius, radius - depth, radius - depth] * teeth
    return Polygon(_ring(cx, cy, radii, 0.0), **kwargs)


@shape(role="arrow.line")
def arrow(x1: float, y1: float, x2: float, y2: float, head: float = DEFAULT_HEAD_SIZE, **kwargs: Any) -> Path:
    """Build a line with an open arrowhead at ``(x2, y2)``.

    Parameters
    ----------
    x1, y1 : float
        Start of the shaft.
    x2, y2 : float
        Tip of the arrow.
    head : float, optional
        Length of each head stroke. Defaults to 10.0.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`;
        ``fill`` defaults to ``"none"``.

    Returns
    -------
    Path
        The arrow as a single path.

    See Also
    --------
    svgwriter.library.paths.arrow_marker : An arrowhead as a reusable marker.

    Examples
    --------
    >>> from svgwriter.library.paths import arrow
    >>> arrow(0, 0, 10, 0).to_string(xml_declaration=False, pretty=False)
    '<path d="M0 0 L10 0 M1.3397 5 L10 0 M1.3397 -5 L10 0" fill="none" class="role-arrow-line"/>'
    """
    angle = math.atan2(y2 - y1, x2 - x1)
    spread = math.radians(ARROW_HEAD_ANGLE)
    builder = PathBuilder().move_to(x1, y1).line_to(x2, y2)
    for side in (-1, 1):
        a = angle + math.pi + side * spread
        builder.move_to(x2 + head * math.cos(a), y2 + head * math.sin(a)).line_to(x2, y2)
    kwargs.setdefault("fill", "none")
    return Path(builder, **kwargs)


@shape
def regular_polygon(
    cx: float,
    cy: float,
    r: float,
    sides: int,
    *,
    rotation: float = 0,
    corner_radius: float = 0,
    inkscape: bool = False,
    **kwargs: Any,
) -> Polygon | Path:
    """Build a regular polygon with optionally rounded corners.

    Parameters
    ----------
    cx, cy : float
        Center.
    r : float
        Distance from the center to each corner before rounding.
    sides : int
        Number of sides, at least 3.
    rotation : float, optional
        Clockwise rotation in degrees; the first corner is at the top when 0. Defaults to 0.
    corner_radius : float, optional
        Radius of the circular fillet at every corner. Defaults to 0 (sharp).
    inkscape : bool, optional
        Build a path carrying Inkscape's polygon parameters (``sodipodi:type="star"``
        with ``inkscape:flatsided="true"``), editable with Inkscape's star tool.
        Defaults to False.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Polygon`
        (:class:`~svgwriter.model.elements.Path` when rounded or `inkscape`).

    Returns
    -------
    Polygon or Path
        The polygon, a path when `corner_radius` rounds it or `inkscape` is set.

    Raises
    ------
    ValueError
        If `sides` is below 3, or `inkscape` is combined with `corner_radius`.

    See Also
    --------
    star : A polygon with notches.

    Examples
    --------
    >>> from svgwriter.library.paths import regular_polygon
    >>> len(regular_polygon(0, 0, 10, 6).points)
    6
    >>> regular_polygon(0, 0, 10, 5, corner_radius=2).tag
    'path'
    >>> regular_polygon(0, 0, 10, 6, inkscape=True).get("inkscape:flatsided")
    'true'
    """
    if sides < MIN_SIDES:
        raise ValueError(f"a polygon needs at least {MIN_SIDES} sides, got {sides}")
    if inkscape:
        return _inkscape_star(cx, cy, r, r * math.cos(math.pi / sides), sides, rotation - QUARTER_TURN, corner_radius,
                              flatsided=True, **kwargs)
    vertices = _ring(cx, cy, [r] * sides, rotation - QUARTER_TURN)
    if corner_radius > 0:
        return rounded_outline(vertices, [corner_radius] * sides, **kwargs)
    return Polygon(vertices, **kwargs)


shape(Polygon.regular, name="polygon")
