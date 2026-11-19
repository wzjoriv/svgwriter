"""
Interpolation between numbers, colors, transforms, path data and whole elements (morphing).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, TypeVar

import numpy as np

from ..color.color import Color, as_color
from ..pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo
from ..pathdata.data import PathData
from ..transform.matrix import Matrix, Point

if TYPE_CHECKING:
    from ..elements.base import Element

__all__ = ["interpolate"]

T = TypeVar("T")
HALF_TURN: Final = 180.0
FULL_TURN: Final = 360.0
DISCRETE_SWITCH: Final = 0.5
GEOMETRY_SKIP: Final = frozenset({"id", "transform", "d", "points"})


def interpolate(a: T, b: T, t: float) -> T:
    """The value a fraction *t* of the way from *a* to *b* (``t=0`` gives *a*, ``t=1`` gives *b*).

    Works on numbers, ``(x, y)`` points and numeric sequences, colors (in
    RGBA), :class:`~svgwriter.transform.Matrix` (translation, rotation, skew
    and scale separately, so turns stay turns), :class:`~svgwriter.PathData`
    and elements. Two elements of the same kind and shape interpolate their
    attributes; anything else is morphed as outlines: both become cubic
    paths with matching subpaths and segment counts. Values that cannot be
    blended (keywords, different strings) switch at ``t = 0.5``, as SMIL's
    discrete mode does.

    Parameters
    ----------
    a, b : object
        Start and end values of the same kind.
    t : float
        Fraction of the way; values outside ``0..1`` extrapolate numbers.

    Returns
    -------
    object
        A new value; neither input is changed.

    See Also
    --------
    svgwriter.Color.mix : Color blending on its own.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.interpolate(0, 10, 0.25)
    2.5
    >>> svg.interpolate(svg.Color.parse("red"), svg.Color.parse("blue"), 0.5).hex
    '#800080'
    >>> svg.interpolate(svg.circle(0, 0, 2), svg.circle(10, 0, 4), 0.5).r
    3.0
    >>> morph = svg.interpolate(svg.rect(0, 0, 10, 10), svg.circle(5, 5, 5), 0.5)
    >>> morph.tag
    'path'
    """
    for kind, blend in _RULES:
        if kind(a) and kind(b):
            return blend(a, b, t)  # type: ignore[no-any-return]
    return a if t < DISCRETE_SWITCH else b


def _number(a: float, b: float, t: float) -> float:
    return float(a) + (float(b) - float(a)) * t


def _sequence(a: Any, b: Any, t: float) -> Any:
    if len(a) != len(b):
        return a if t < DISCRETE_SWITCH else b
    values = [interpolate(x, y, t) for x, y in zip(a, b, strict=True)]
    return Point(*values) if isinstance(a, Point) else type(a)(values) if isinstance(a, tuple) else values


def _color(a: Any, b: Any, t: float) -> Color:
    first, second = as_color(a), as_color(b)
    return Color(*(_number(x, y, t) for x, y in zip(first.rgba, second.rgba, strict=True)))


def _angle(a: float, b: float, t: float) -> float:
    turn = (b - a + HALF_TURN) % FULL_TURN - HALF_TURN
    return a + turn * t


def _matrix(a: Matrix, b: Matrix, t: float) -> Matrix:
    (ax, ay, ar, ak, asx, asy), (bx, by, br, bk, bsx, bsy) = a.decompose(), b.decompose()
    return (Matrix.translate(_number(ax, bx, t), _number(ay, by, t)) @ Matrix.rotate(_angle(ar, br, t))
            @ Matrix.skew_x(_number(ak, bk, t)) @ Matrix.scale(_number(asx, bsx, t), _number(asy, bsy, t)))


def _is_color(value: object) -> bool:
    if isinstance(value, Color):
        return True
    if isinstance(value, str):
        try:
            as_color(value)
        except ValueError:
            return False
        return True
    return False


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float, np.floating, np.integer)) and not isinstance(value, bool)


def _is_sequence(value: object) -> bool:
    return isinstance(value, (tuple, list)) and all(_is_number(v) or _is_sequence(v) for v in value)


def _array(a: Any, b: Any, t: float) -> Any:
    first, second = np.asarray(getattr(a, "array", a), dtype=float), np.asarray(getattr(b, "array", b), dtype=float)
    if first.shape != second.shape:
        return a if t < DISCRETE_SWITCH else b
    mixed = first + (second - first) * t
    return type(a)(mixed) if hasattr(a, "array") else mixed


def _is_array(value: object) -> bool:
    return isinstance(value, np.ndarray) or isinstance(getattr(value, "array", None), np.ndarray)


def _is_element(value: object) -> bool:
    from ..elements.base import Element

    return isinstance(value, Element)


_RULES: Final[list[tuple[Callable[[object], bool], Callable[[Any, Any, float], Any]]]] = [
    (_is_number, _number),
    (lambda v: isinstance(v, Matrix), _matrix),
    (lambda v: isinstance(v, PathData), lambda a, b, t: _paths(a, b, t)),
    (_is_array, _array),
    (_is_element, lambda a, b, t: _elements(a, b, t)),
    (_is_sequence, _sequence),
    (_is_color, _color),
]


def _cubics(data: PathData) -> list[tuple[np.ndarray, bool]]:
    """Subpaths as ``(n, 4, 2)`` cubic segments (start, control, control, end) and a closed flag."""
    from ._skia import from_skia, to_skia

    result: list[tuple[np.ndarray, bool]] = []
    segments: list[list[tuple[float, float]]] = []
    start = here = (0.0, 0.0)
    closed = False

    def flush() -> None:
        if segments:
            result.append((np.array(segments, dtype=float), closed))

    for command in from_skia(to_skia(data)):
        if isinstance(command, MoveTo):
            flush()
            segments, closed = [], False
            start = here = (command.x, command.y)
            continue
        if isinstance(command, ClosePath):
            if here != start:
                segments.append([here, *_line(here, start)])
            closed, here = True, start
            continue
        end = (command.x, command.y)
        if isinstance(command, LineTo):
            controls = _line(here, end)[:2]
        elif isinstance(command, QuadTo):
            q = (command.x1, command.y1)
            controls = [_mix(here, q, 2 / 3), _mix(end, q, 2 / 3)]
        else:
            assert isinstance(command, CurveTo)
            controls = [(command.x1, command.y1), (command.x2, command.y2)]
        segments.append([here, *controls, end])
        here = end
    flush()
    return result


def _mix(p: tuple[float, float], q: tuple[float, float], t: float) -> tuple[float, float]:
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _line(p: tuple[float, float], q: tuple[float, float]) -> list[tuple[float, float]]:
    return [_mix(p, q, 1 / 3), _mix(p, q, 2 / 3), q]


def _split(segment: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """De Casteljau split of one cubic at its middle."""
    p0, p1, p2, p3 = segment
    a, b, c = (p0 + p1) / 2, (p1 + p2) / 2, (p2 + p3) / 2
    d, e = (a + b) / 2, (b + c) / 2
    m = (d + e) / 2
    return np.array([p0, a, d, m]), np.array([m, e, c, p3])


def _grow(segments: np.ndarray, count: int) -> np.ndarray:
    """Split the longest segments until there are *count* of them."""
    items = list(segments)
    while len(items) < count:
        longest = max(range(len(items)), key=lambda i: float(np.linalg.norm(items[i][3] - items[i][0])))
        items[longest:longest + 1] = _split(items[longest])
    return np.array(items)


def _rotate_to_match(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """For closed rings, start *b* at the segment whose start is nearest *a*'s, so the morph does not twist."""
    starts_a, starts_b = a[:, 0], b[:, 0]
    best = min(range(len(b)), key=lambda k: float(np.sum((np.roll(starts_b, -k, axis=0) - starts_a) ** 2)))
    return np.roll(b, -best, axis=0)


def _point_ring(center: np.ndarray, count: int) -> np.ndarray:
    return np.repeat(center[None, None, :], count, axis=0).repeat(4, axis=1)


def _paths(a: PathData, b: PathData, t: float) -> PathData:
    first, second = _cubics(a), _cubics(b)
    for mine, other in ((first, second), (second, first)):
        while len(mine) < len(other):
            ring, closed = other[len(mine)]
            center = (ring[:, 0].min(axis=0) + ring[:, 0].max(axis=0)) / 2
            mine.append((_point_ring(center, len(ring)), closed))
    commands: list[Any] = []
    for (ra, ca), (rb, cb) in zip(first, second, strict=True):
        count = max(len(ra), len(rb))
        ra, rb = _grow(ra, count), _grow(rb, count)
        if ca and cb:
            rb = _rotate_to_match(ra, rb)
        mixed = ra + (rb - ra) * t
        commands.append(MoveTo(*mixed[0, 0]))
        commands += [CurveTo(*s[1], *s[2], *s[3]) for s in mixed]
        if ca or cb:
            commands.append(ClosePath())
    return PathData(commands)


def _same_shape(a: Element, b: Element) -> bool:
    if type(a) is not type(b) or len(a.children) or len(b.children):
        return False
    for key in set(a.attributes) | set(b.attributes):
        x, y = a.attributes.get(key), b.attributes.get(key)
        if key == "points" and not (_is_array(x) and _is_array(y) and np.shape(x.array) == np.shape(y.array)):  # type: ignore[union-attr]
            return False
        if key == "d" and not (isinstance(x, PathData) and isinstance(y, PathData)):
            return False
    return True


def _elements(a: Element, b: Element, t: float) -> Element:
    if _same_shape(a, b):
        result = a.clone()
        for key in set(a.attributes) | set(b.attributes):
            if key in ("id", "transform"):
                continue
            result.attributes.pop(key, None)
            value = interpolate(a.attributes.get(key), b.attributes.get(key), t)
            if value is not None:
                result.set(key, value)
    else:
        result = _morph(a, b, t)
    if hasattr(a, "t") and hasattr(b, "t"):
        pivot = interpolate(a.anchor, b.anchor, t)  # type: ignore[attr-defined]
        about = Matrix.translate(pivot.x, pivot.y)
        result.t = about @ _matrix(about.inverse() @ a.t @ about, about.inverse() @ b.t @ about, t) @ about.inverse()  # type: ignore[attr-defined]
    return result


def _geometry(element: Element) -> frozenset[str]:
    return getattr(type(element), "geometry_attributes", frozenset())


def _morph(a: Element, b: Element, t: float) -> Element:
    """Both as local outlines, blended; paint and other attributes blend or switch."""
    from ..elements.shapes import Path

    data = _paths(a.local_outline(), b.local_outline(), t)  # type: ignore[attr-defined]
    path = Path(data)
    geometry = GEOMETRY_SKIP | _geometry(a) | _geometry(b)
    for key in (set(a.attributes) | set(b.attributes)) - geometry:
        value = interpolate(a.attributes.get(key), b.attributes.get(key), t)
        if value is not None:
            path.set(key, value)
    return path
