"""
Filled symbol presets: heart, callout and cross.
"""

from __future__ import annotations

from typing import Any

from ...model.elements.shapes import Path, Polygon
from ...model.pathdata.builder import PathBuilder
from ..preset import shape
from ._constants import (
    CALLOUT_RADIUS,
    CALLOUT_TAIL_RATIO,
    CROSS_THICKNESS_RATIO,
    HEART_CURVES,
    HEART_MIDLINE,
    HEART_NOTCH,
)
from ._rounded import rounded_outline

__all__ = ["callout", "cross", "heart"]


@shape
def heart(cx: float, cy: float, size: float, **kwargs: Any) -> Path:
    """Build a heart made of cubic curves, point down.

    Parameters
    ----------
    cx, cy : float
        Center of the bounding box.
    size : float
        Width of the heart; its height is 95% of that.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`.

    Returns
    -------
    Path
        The closed heart.

    See Also
    --------
    star : A star polygon.

    Examples
    --------
    >>> from svgwriter.library.paths import heart
    >>> box = heart(50, 50, 40).bbox
    >>> round(box.width, 1), round(box.height, 1)
    (40.0, 38.0)
    """

    def place(point: tuple[float, float], side: int) -> tuple[float, float]:
        return cx + side * point[0] * size, cy + (point[1] - HEART_MIDLINE) * size

    builder = PathBuilder().move_to(*place(HEART_NOTCH, 1))
    chain = [HEART_NOTCH, *(curve[2] for curve in HEART_CURVES)]
    for first, second, end in HEART_CURVES:
        builder.curve_to(*place(first, 1), *place(second, 1), *place(end, 1))
    for index in range(len(HEART_CURVES) - 1, -1, -1):
        first, second, _ = HEART_CURVES[index]
        builder.curve_to(*place(second, -1), *place(first, -1), *place(chain[index], -1))
    builder.close()
    return Path(builder, **kwargs)


@shape(role="box")
def callout(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    tail: tuple[float, float],
    corner_radius: float = CALLOUT_RADIUS,
    **kwargs: Any,
) -> Path:
    """Build a speech bubble whose tail points at *tail*.

    Parameters
    ----------
    x, y : float
        Top-left corner of the bubble body.
    width, height : float
        Size of the bubble body.
    tail : (float, float)
        The point the tail touches. The tail leaves the side nearest to it.
    corner_radius : float, optional
        Radius of the body's corners. Defaults to 8.0.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Path`.

    Returns
    -------
    Path
        The closed bubble, body and tail in one outline.

    See Also
    --------
    svgwriter.Rect : A plain rectangle.

    Examples
    --------
    >>> from svgwriter.library.paths import callout
    >>> bubble = callout(0, 0, 100, 40, tail=(20, 70))
    >>> bubble.bbox.height
    70.0
    """
    tx, ty = tail
    radius = min(corner_radius, width / 2, height / 2)
    reach = {"top": y - ty, "bottom": ty - (y + height), "left": x - tx, "right": tx - (x + width)}
    side = max(reach, key=lambda name: reach[name])
    base = min(width, height) * CALLOUT_TAIL_RATIO
    corners = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    if side in ("top", "bottom"):
        span = min(base, width - 2 * radius)
        mid = min(max(tx, x + radius + span / 2), x + width - radius - span / 2)
        edge = y if side == "top" else y + height
        wings = [(mid - span / 2, edge), (tx, ty), (mid + span / 2, edge)]
        wings = wings if side == "top" else wings[::-1]
    else:
        span = min(base, height - 2 * radius)
        mid = min(max(ty, y + radius + span / 2), y + height - radius - span / 2)
        edge = x + width if side == "right" else x
        wings = [(edge, mid - span / 2), (tx, ty), (edge, mid + span / 2)]
        wings = wings if side == "right" else wings[::-1]
    slot = {"top": 1, "right": 2, "bottom": 3, "left": 4}[side]
    points = [*corners[:slot], *wings, *corners[slot:]]
    radii = [radius] * slot + [0] * len(wings) + [radius] * (len(corners) - slot)
    return rounded_outline(points, radii, **kwargs)


@shape
def cross(cx: float, cy: float, size: float, *, thickness: float | None = None, **kwargs: Any) -> Polygon:
    """Build a plus sign.

    Parameters
    ----------
    cx, cy : float
        Center.
    size : float
        Full width and height of the sign.
    thickness : float, optional
        Width of each arm. Defaults to a third of `size`.
    **kwargs
        Presentation attributes forwarded to :class:`~svgwriter.model.elements.Polygon`.

    Returns
    -------
    Polygon
        The 12-sided outline.

    Raises
    ------
    ValueError
        If `thickness` is not between 0 and `size`.

    See Also
    --------
    star : Another symbol preset.

    Examples
    --------
    >>> from svgwriter.library.paths import cross
    >>> len(cross(0, 0, 30).points)
    12
    >>> cross(0, 0, 30, thickness=6).bbox.width
    30.0
    """
    thickness = size * CROSS_THICKNESS_RATIO if thickness is None else thickness
    if not 0 < thickness <= size:
        raise ValueError(f"thickness must be between 0 and size, got {thickness}")
    a, b = thickness / 2, size / 2
    outline = [(a, -b), (a, -a), (b, -a), (b, a), (a, a), (a, b), (-a, b), (-a, a), (-b, a), (-b, -a), (-a, -a), (-a, -b)]
    return Polygon([(cx + dx, cy + dy) for dx, dy in outline], **kwargs)
