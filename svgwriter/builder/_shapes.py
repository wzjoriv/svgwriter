"""
Composite shapes registered by name for the CLI and plugins.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable
from typing import Any, Final, TypeVar

from .._internal._registry import Registry
from .._internal._typing import P
from ..elements.base import Element
from ..elements.shapes import Path, Polygon
from ..pathdata.builder import PathBuilder

__all__ = ["SHAPES", "arrow", "gear", "regular_polygon", "shape_factory", "star"]

E = TypeVar("E", bound=Element)

SHAPES: Final[Registry[Callable[..., Element]]] = Registry("shape")
FULL_TURN: Final = 360.0
QUARTER_TURN: Final = 90.0
DEFAULT_STAR_POINTS: Final = 5
DEFAULT_INNER_RATIO: Final = 0.5
DEFAULT_HEAD_SIZE: Final = 10.0
ARROW_HEAD_ANGLE: Final = 30.0
DEFAULT_TEETH: Final = 12
TOOTH_DEPTH_RATIO: Final = 0.15


def shape_factory(name: str) -> Callable[[Callable[P, E]], Callable[P, E]]:
    """Register a function returning an element under *name*.

    The wrapper checks the return type, so plugins fail loudly. Registered
    shapes are listed by ``python -m svgwriter shapes`` and drawn by
    ``python -m svgwriter draw``.

    Parameters
    ----------
    name : str
        The name to register the shape under.

    Returns
    -------
    callable
        A decorator that registers the function and returns the checking wrapper.

    Raises
    ------
    ValueError
        If `name` is already registered.
    TypeError
        When the decorated function is called and does not return an element.

    See Also
    --------
    SHAPES : The registry of shapes.

    Examples
    --------
    >>> from svgwriter import Circle
    >>> from svgwriter.builder import shape_factory
    >>> from svgwriter.builder import SHAPES
    >>> @shape_factory("disc")
    ... def disc(cx, cy, r, **kwargs):
    ...     return Circle(cx, cy, r, **kwargs)
    >>> disc(0, 0, 2).tag
    'circle'
    >>> _ = SHAPES.remove("disc")
    """

    def decorate(func: Callable[P, E]) -> Callable[P, E]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> E:
            result = func(*args, **kwargs)
            if not isinstance(result, Element):
                raise TypeError(f"shape {name!r} returned {type(result).__name__}")
            return result

        SHAPES.add(name, wrapper)
        return wrapper

    return decorate


def _ring(cx: float, cy: float, radii: list[float], rotation: float) -> list[tuple[float, float]]:
    count = len(radii)
    points = []
    for index, radius in enumerate(radii):
        angle = math.radians(rotation + FULL_TURN * index / count)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


@shape_factory("star")
def star(
    cx: float,
    cy: float,
    outer: float,
    inner: float | None = None,
    points: int = DEFAULT_STAR_POINTS,
    **kwargs: Any,
) -> Polygon:
    """Build a star polygon with *points* tips, pointing up.

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
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.elements.Polygon`.

    Returns
    -------
    Polygon
        The star.

    See Also
    --------
    regular_polygon : A polygon without notches.

    Examples
    --------
    >>> from svgwriter.builder import star
    >>> len(star(50, 50, 40).points)
    10
    """
    inner = outer * DEFAULT_INNER_RATIO if inner is None else inner
    return Polygon(_ring(cx, cy, [outer, inner] * points, -QUARTER_TURN), **kwargs)


@shape_factory("polygon")
def regular_polygon(cx: float, cy: float, radius: float, sides: int = 6, **kwargs: Any) -> Polygon:
    """Build a regular polygon with one vertex pointing up.

    Parameters
    ----------
    cx, cy : float
        Center.
    radius : float
        Distance from the center to each vertex.
    sides : int, optional
        Number of sides. Defaults to 6.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.elements.Polygon`.

    Returns
    -------
    Polygon
        The polygon.

    See Also
    --------
    star : A polygon with alternating radii.

    Examples
    --------
    >>> from svgwriter.builder import regular_polygon
    >>> regular_polygon(0, 0, 10, sides=3).to_string(xml_declaration=False, pretty=False)
    '<polygon points="0,-10 8.6603,5 -8.6603,5"/>'
    """
    return Polygon(_ring(cx, cy, [radius] * sides, -QUARTER_TURN), **kwargs)


@shape_factory("gear")
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
        Presentation attributes forwarded to :class:`~svgwriter.elements.Polygon`.

    Returns
    -------
    Polygon
        The gear; the tooth root sits 15% of `radius` below the tips.

    See Also
    --------
    star : Another composite polygon.

    Examples
    --------
    >>> from svgwriter.builder import gear
    >>> len(gear(0, 0, 20, teeth=8).points)
    32
    """
    depth = radius * TOOTH_DEPTH_RATIO
    radii = [radius, radius, radius - depth, radius - depth] * teeth
    return Polygon(_ring(cx, cy, radii, 0.0), **kwargs)


@shape_factory("arrow")
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
        Presentation attributes forwarded to :class:`~svgwriter.elements.Path`;
        ``fill`` defaults to ``"none"``.

    Returns
    -------
    Path
        The arrow as a single path.

    See Also
    --------
    svgwriter.builder.arrow_marker : An arrowhead as a reusable marker.

    Examples
    --------
    >>> from svgwriter.builder import arrow
    >>> arrow(0, 0, 10, 0).to_string(xml_declaration=False, pretty=False)
    '<path d="M0 0 L10 0 M1.3397 5 L10 0 M1.3397 -5 L10 0" fill="none"/>'
    """
    angle = math.atan2(y2 - y1, x2 - x1)
    spread = math.radians(ARROW_HEAD_ANGLE)
    builder = PathBuilder().move_to(x1, y1).line_to(x2, y2)
    for side in (-1, 1):
        a = angle + math.pi + side * spread
        builder.move_to(x2 + head * math.cos(a), y2 + head * math.sin(a)).line_to(x2, y2)
    kwargs.setdefault("fill", "none")
    return Path(builder, **kwargs)
