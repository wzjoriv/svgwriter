"""
Endpoint-to-center conversion for elliptical arcs (SVG 1.1, F.6.5).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..transform.matrix import Point
from ._constants import FULL_TURN

__all__ = ["CenterArc", "endpoint_to_center"]


@dataclass(frozen=True)
class CenterArc:
    """An elliptical arc in center parameterization.

    Describes the arc by the ellipse centre, radii and rotation plus a start
    angle and a signed sweep, which is easier to sample than the endpoint form.

    Parameters
    ----------
    cx, cy : float
        Centre of the ellipse.
    rx, ry : float
        Radii of the ellipse along its own axes.
    rotation : float
        Rotation of the ellipse's x axis, in degrees.
    start_angle : float
        Angle of the arc's first point on the ellipse, in radians.
    sweep : float
        Signed angular extent in radians; positive is clockwise in SVG's
        y-down coordinate system.

    See Also
    --------
    endpoint_to_center : Build a `CenterArc` from SVG endpoint parameters.

    Examples
    --------
    >>> from svgwriter.model.pathdata import CenterArc
    >>> arc = CenterArc(0, 0, 5, 5, 0, 0.0, 3.141592653589793)
    >>> arc.sweep > 0
    True
    """

    cx: float
    cy: float
    rx: float
    ry: float
    rotation: float
    start_angle: float
    sweep: float

    def point_at(self, t: float) -> Point:
        """Return the point at parameter `t` along the arc.

        Parameters
        ----------
        t : float
            Position along the arc, from 0 (start) to 1 (end).

        Returns
        -------
        Point
            The point on the arc.

        Examples
        --------
        >>> from svgwriter.model.pathdata import endpoint_to_center
        >>> from svgwriter.model.transform import Point
        >>> arc = endpoint_to_center(Point(0, 0), Point(10, 0), 5, 5, 0, False, True)
        >>> p = arc.point_at(0.5)
        >>> round(p.x, 6), round(p.y, 6)
        (5.0, -5.0)
        """
        angle = self.start_angle + self.sweep * t
        phi = math.radians(self.rotation)
        cos_phi, sin_phi = math.cos(phi), math.sin(phi)
        x = self.rx * math.cos(angle)
        y = self.ry * math.sin(angle)
        return Point(cos_phi * x - sin_phi * y + self.cx, sin_phi * x + cos_phi * y + self.cy)

    def sample(self, count: int) -> list[Point]:
        """Return evenly spaced points along the arc.

        Parameters
        ----------
        count : int
            Number of segments; the result has ``count + 1`` points including both ends.

        Returns
        -------
        list of Point
            Points from the start to the end of the arc.

        Examples
        --------
        >>> from svgwriter.model.pathdata import endpoint_to_center
        >>> from svgwriter.model.transform import Point
        >>> arc = endpoint_to_center(Point(0, 0), Point(10, 0), 5, 5, 0, False, True)
        >>> len(arc.sample(4))
        5
        """
        return [self.point_at(i / count) for i in range(count + 1)]


def _angle(ux: float, uy: float, vx: float, vy: float) -> float:
    dot = ux * vx + uy * vy
    length = math.hypot(ux, uy) * math.hypot(vx, vy)
    angle = math.acos(max(-1.0, min(1.0, dot / length)))
    return -angle if ux * vy - uy * vx < 0 else angle


def endpoint_to_center(
    start: Point,
    end: Point,
    rx: float,
    ry: float,
    rotation: float,
    large_arc: bool,
    sweep: bool,
) -> CenterArc | None:
    """Convert endpoint arc parameters to a `CenterArc`.

    Implements the conversion from SVG 1.1 appendix F.6.5. Radii that are too
    small to span the endpoints are scaled up as the specification requires.

    Parameters
    ----------
    start, end : Point
        The arc's start and end points.
    rx, ry : float
        Ellipse radii.
    rotation : float
        Rotation of the ellipse's x axis, in degrees.
    large_arc : bool
        Choose the arc spanning more than half the ellipse.
    sweep : bool
        Choose the arc drawn in the positive-angle (clockwise) direction.

    Returns
    -------
    CenterArc or None
        The centre form, or ``None`` when the arc degenerates to a straight
        line (zero radius or coincident endpoints).

    See Also
    --------
    CenterArc : The returned parameterization.

    Examples
    --------
    >>> from svgwriter.model.pathdata import endpoint_to_center
    >>> from svgwriter.model.transform import Point
    >>> arc = endpoint_to_center(Point(0, 0), Point(10, 0), 5, 5, 0, False, True)
    >>> arc.cx, arc.cy
    (5.0, 0.0)
    >>> endpoint_to_center(Point(0, 0), Point(0, 0), 5, 5, 0, False, True) is None
    True
    """
    if start == end or rx == 0 or ry == 0:
        return None
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rotation)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    dx, dy = (start.x - end.x) / 2.0, (start.y - end.y) / 2.0
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    scale = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if scale > 1.0:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)

    numerator = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    factor = math.sqrt(max(0.0, numerator / denominator))
    if large_arc == sweep:
        factor = -factor
    cxp = factor * rx * y1p / ry
    cyp = -factor * ry * x1p / rx

    cx = cos_phi * cxp - sin_phi * cyp + (start.x + end.x) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (start.y + end.y) / 2.0

    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    vx, vy = (-x1p - cxp) / rx, (-y1p - cyp) / ry
    theta = _angle(1.0, 0.0, ux, uy)
    delta = _angle(ux, uy, vx, vy) % FULL_TURN
    if not sweep and delta > 0:
        delta -= FULL_TURN
    return CenterArc(cx, cy, rx, ry, rotation, theta, delta)
