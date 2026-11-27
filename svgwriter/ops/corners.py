"""
Sharp corners of an outline, and replacing them with circular or quadratic fillets.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal, NamedTuple

import numpy as np

from ..model.pathdata.commands import ArcTo, ClosePath, CurveTo, LineTo, MoveTo, PathCommand, QuadTo
from ..model.pathdata.data import PathData
from ..model.transform.matrix import Point
from ..model.units.angle import Angle
from ._constants import ARC_HANDLE, CORNER_TOLERANCE, LENGTH_SEARCH_STEPS, PIXEL_EPSILON
from ._skia import Geometry, from_skia, geometry_data, to_skia

__all__ = ["Corner", "CornerFilter", "Fillet", "corners", "round_corners"]

Fillet = Literal["arc", "quad"]
"""How a rounded corner is drawn: a circular arc or a quadratic curve through the old vertex's pull."""


class Corner(NamedTuple):
    """A sharp vertex of an outline.

    Parameters
    ----------
    index : int
        The vertex number: segment end points counted in drawing order across
        all subpaths, starting at 0 with each subpath's first point.
    point : Point
        Where the vertex is.
    angle : Angle
        The turn the outline makes there; positive turns towards +y
        (clockwise on screen), 180 degrees is a full reversal.

    Examples
    --------
    >>> from svgwriter.ops import corners
    >>> corners("M0 0 L10 0 L10 10")[0]
    Corner(index=1, point=Point(x=10.0, y=0.0), angle=Angle(value=90.0, unit='deg'))
    """

    index: int
    point: Point
    angle: Angle


CornerFilter = Callable[[Corner], bool] | Iterable[int] | None
"""Which corners to round: all (None), those a predicate accepts, or the listed vertex numbers."""


@dataclass
class _Subpath:
    segments: list[np.ndarray]
    closed: bool


def _segment_point(controls: np.ndarray, t: float) -> np.ndarray:
    points = controls
    while len(points) > 1:
        points = points[:-1] + (points[1:] - points[:-1]) * t
    return points[0]


def _split(controls: np.ndarray, t: float) -> tuple[np.ndarray, np.ndarray]:
    left, right, points = [controls[0]], [controls[-1]], controls
    while len(points) > 1:
        points = points[:-1] + (points[1:] - points[:-1]) * t
        left.append(points[0])
        right.append(points[-1])
    return np.array(left), np.array(right[::-1])


def _cumulative(controls: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    steps = np.linspace(0.0, 1.0, 2 if len(controls) == 2 else LENGTH_SEARCH_STEPS + 1)
    points = np.array([_segment_point(controls, t) for t in steps])
    return steps, np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(points, axis=0).T))])


def _length(controls: np.ndarray) -> float:
    return float(_cumulative(controls)[1][-1])


def _parameter(controls: np.ndarray, distance: float) -> float:
    steps, walked = _cumulative(controls)
    return float(np.interp(distance, walked, steps))


def _direction(controls: np.ndarray, at_end: bool) -> np.ndarray:
    points = controls[::-1] if at_end else controls
    for other in points[1:]:
        delta = other - points[0]
        if math.hypot(*delta) > PIXEL_EPSILON:
            return -delta if at_end else delta
    return np.zeros(2)


def _cross(first: np.ndarray, second: np.ndarray) -> float:
    return float(first[0] * second[1] - first[1] * second[0])


def _subpaths(item: Geometry) -> list[_Subpath]:
    data, evenodd = geometry_data(item)
    result: list[_Subpath] = []
    start = pen = np.zeros(2)
    for command in from_skia(to_skia(data, evenodd=evenodd)):
        if isinstance(command, MoveTo):
            start = pen = np.array([command.x, command.y])
            result.append(_Subpath([], False))
            continue
        if isinstance(command, ClosePath):
            if math.hypot(*(start - pen)) > PIXEL_EPSILON:
                result[-1].segments.append(np.array([pen, start]))
            result[-1].closed, pen = True, start
            continue
        if isinstance(command, LineTo):
            controls = np.array([pen, [command.x, command.y]])
        elif isinstance(command, QuadTo):
            controls = np.array([pen, [command.x1, command.y1], [command.x, command.y]])
        else:
            assert isinstance(command, CurveTo)
            controls = np.array([pen, [command.x1, command.y1], [command.x2, command.y2], [command.x, command.y]])
        if np.ptp(controls, axis=0).max() > PIXEL_EPSILON:
            result[-1].segments.append(controls)
        pen = controls[-1]
    return [piece for piece in result if piece.segments]


def _turns(piece: _Subpath) -> dict[int, float]:
    """Turning angle in radians at each joint, keyed by the index of the segment leaving it."""
    count = len(piece.segments)
    turns = {}
    for joint in range(0 if piece.closed else 1, count):
        incoming, outgoing = _direction(piece.segments[joint - 1], True), _direction(piece.segments[joint], False)
        turns[joint] = math.atan2(_cross(incoming, outgoing), float(incoming @ outgoing))
    return turns


def _vertex_counts(pieces: list[_Subpath]) -> list[int]:
    return [len(piece.segments) + (0 if piece.closed else 1) for piece in pieces]


def corners(item: Geometry, tolerance: Angle | float = CORNER_TOLERANCE) -> list[Corner]:
    """The sharp vertices of an outline, where the direction jumps.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline.
    tolerance : Angle or float, optional
        Turns at or below this (degrees for a number) count as smooth. Defaults to 0.01 degrees.

    Returns
    -------
    list of Corner
        Index, position and turning angle of each corner, in drawing order.

    See Also
    --------
    round_corners : Replace corners with fillets.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import corners
    >>> [c.index for c in corners(svg.rect(0, 0, 4, 2))]
    [0, 1, 2, 3]
    >>> corners(svg.circle(0, 0, 5))
    []
    """
    limit = math.radians(float(Angle.parse(tolerance)))
    found, offset = [], 0
    for piece, count in zip(pieces := _subpaths(item), _vertex_counts(pieces), strict=True):
        for joint, turn in _turns(piece).items():
            if abs(turn) > limit:
                x, y = piece.segments[joint][0]
                found.append(Corner(offset + joint, Point(float(x), float(y)), Angle(math.degrees(turn))))
        offset += count
    return found


def _selected(found: list[Corner], where: CornerFilter) -> set[int]:
    if where is None:
        return {corner.index for corner in found}
    if callable(where):
        return {corner.index for corner in found if where(corner)}
    wanted, known = set(where), {corner.index for corner in found}
    if wanted - known:
        raise ValueError(f"vertices {sorted(wanted - known)} are not corners; corners are {sorted(known)}")
    return wanted


def _command(controls: np.ndarray) -> PathCommand:
    values = [float(v) for v in controls[1:].ravel()]
    return (LineTo, QuadTo, CurveTo)[len(controls) - 2](*values)


def _trimmed(controls: np.ndarray, head: float, tail: float) -> np.ndarray:
    total = _length(controls)
    end = _parameter(controls, total - tail) if tail else 1.0
    if end < 1.0:
        controls = _split(controls, end)[0]
    if head:
        controls = _split(controls, _parameter(controls, head))[1]
    return controls


def _unit(vector: np.ndarray) -> np.ndarray:
    return vector / max(math.hypot(*vector), PIXEL_EPSILON)


def _tangent(trimmed: np.ndarray, original: np.ndarray, at_end: bool) -> np.ndarray:
    direction = _direction(trimmed, at_end)
    return _unit(direction if direction.any() else _direction(original, at_end))


def _fillet(before: tuple[np.ndarray, np.ndarray], after: tuple[np.ndarray, np.ndarray], fillet: Fillet) -> PathCommand:
    """The curve from the end of the trimmed *before* to the start of the trimmed *after*, tangent to both.

    Each side is the trimmed segment with its original.
    """
    start, end, vertex = before[0][-1], after[0][0], after[1][0]
    straight = len(before[1]) == len(after[1]) == 2
    incoming, outgoing = _tangent(*before, True), _tangent(*after, False)
    turn = abs(math.atan2(_cross(incoming, outgoing), float(incoming @ outgoing)))
    chord = math.hypot(*(end - start))
    if fillet == "quad":
        denominator = _cross(incoming, outgoing)
        control = vertex if straight or abs(denominator) < PIXEL_EPSILON else (
            start + incoming * _cross(end - start, outgoing) / denominator)
        return QuadTo(*(float(v) for v in control), *(float(v) for v in end))
    radius = chord / (2 * math.sin(turn / 2))
    if straight:
        return ArcTo(radius, radius, 0, False, _cross(incoming, outgoing) > 0, *(float(v) for v in end))
    handle = radius * ARC_HANDLE * math.tan(turn / 4)
    return CurveTo(*(float(v) for v in (*(start + incoming * handle), *(end - outgoing * handle), *end)))


def round_corners(item: Geometry, radius: float, where: CornerFilter = None, *, fillet: Fillet = "arc") -> PathData:
    """Replace sharp corners with fillets of *radius*.

    A fillet shrinks when its neighbours are too short for the radius (sharing
    a side with another fillet leaves each half of it), so the outline never
    overlaps itself. Fillets between straight sides are exact circular arcs;
    next to curves they are cubic curves that leave and join the curves
    smoothly, a fillet's reach from the vertex.

    Parameters
    ----------
    item : shape, text, PathData or str
        The outline.
    radius : float
        Fillet radius in user units.
    where : callable, iterable of int or None, optional
        Which corners: None for all, a predicate taking a `Corner`, or vertex
        numbers (``Corner.index``). Defaults to None.
    fillet : {"arc", "quad"}, optional
        Draw a circular arc, or a quadratic curve pulled towards the old vertex. Defaults to "arc".

    Returns
    -------
    PathData
        The rounded outline.

    Raises
    ------
    ValueError
        If a listed vertex is not a corner.

    See Also
    --------
    corners : Find the corners and their numbers.

    Examples
    --------
    >>> from svgwriter.ops import round_corners
    >>> str(round_corners("M0 0 H10 V10", 2))
    'M0 0 L8 0 A2 2 0 0 1 10 2 L10 10'
    """
    found = corners(item)
    chosen = _selected(found, where)
    turn_at = {corner.index: abs(corner.angle.radians) for corner in found}
    commands: list[PathCommand] = []
    offset = 0
    for piece, count in zip(pieces := _subpaths(item), _vertex_counts(pieces), strict=True):
        segments, size = piece.segments, len(piece.segments)
        lengths = [_length(segment) for segment in segments]
        rounded = {joint: offset + joint in chosen for joint in range(count)}
        reach: dict[int, float] = {}
        for joint, is_rounded in rounded.items():
            if not is_rounded:
                continue
            before, after = (joint - 1) % size, joint % size
            room_before = lengths[before] / (2 if rounded.get((joint - 1) % count, False) else 1)
            room_after = lengths[after] / (2 if rounded.get((joint + 1) % count, False) else 1)
            reach[joint] = min(radius * math.tan(turn_at[offset + joint] / 2), room_before, room_after)
        trimmed = [_trimmed(segment, reach.get(index, 0.0), reach.get((index + 1) % count if piece.closed else index + 1, 0.0))
                   for index, segment in enumerate(segments)]
        commands.append(MoveTo(*(float(v) for v in trimmed[0][0])))
        for index, segment in enumerate(trimmed):
            if np.ptp(segment, axis=0).max() > PIXEL_EPSILON:
                commands.append(_command(segment))
            joint = (index + 1) % size if piece.closed else index + 1
            if joint in reach:
                commands.append(_fillet((segment, segments[index]), (trimmed[joint], segments[joint]), fillet))
        if piece.closed:
            commands.append(ClosePath())
        offset += count
    return PathData(commands)
