"""
Outline correspondence for morphing: contours matched by role and place, resampled and started where they agree.
"""

from __future__ import annotations

import functools
import math
from typing import Any

import numpy as np

from .._internal._flatten import polylines
from ..pathdata.commands import ClosePath, LineTo, MoveTo
from ..pathdata.data import PathData
from ._constants import MORPH_CORNER, MORPH_FLATNESS, MORPH_MAX_POINTS, MORPH_MIN_POINTS, MORPH_SPACING

__all__ = ["blend_outlines", "correspond"]

Contour = tuple[np.ndarray, bool]
Pair = tuple[np.ndarray, np.ndarray, bool]


def blend_outlines(a: PathData, b: PathData, t: float) -> PathData:
    """The outline a fraction *t* of the way from *a* to *b*, through their matched contours.

    Parameters
    ----------
    a, b : PathData
        Start and end outlines.
    t : float
        Fraction of the way.

    Returns
    -------
    PathData
        Straight-segment subpaths, dense enough to look smooth, one per matched contour pair.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._morph import blend_outlines
    >>> square, diamond = svg.PathData("M0 0H10V10H0Z"), svg.PathData("M5 -2L12 5L5 12L-2 5Z")
    >>> len(blend_outlines(square, diamond, 0.5).subpaths())
    1
    """
    commands: list[Any] = []
    for first, second, closed in correspond(a, b):
        mixed = first + (second - first) * t
        commands.append(MoveTo(*mixed[0]))
        commands += [LineTo(*p) for p in mixed[1:]]
        if closed:
            commands.append(ClosePath())
    return PathData(commands)


def correspond(a: PathData, b: PathData) -> list[Pair]:
    """Matched point rings of *a* and *b*: same counts, same winding, best-fitting start points.

    Closed contours are sorted into outlines and holes (by containment) and
    wound consistently, so holes stay holes for the nonzero rule. Outlines pair
    with outlines and holes with holes, nearest in place and size first; a
    contour left without a partner grows from (or shrinks to) its own centroid.
    Each pair is resampled by arc length to one point count, keeping sharp
    corners, and the second ring is turned to the start that moves the points
    least, so the in-between shapes do not twist.

    Parameters
    ----------
    a, b : PathData
        Start and end outlines.

    Returns
    -------
    list of (ndarray, ndarray, bool)
        For each contour pair, the ``(n, 2)`` points of each side and whether it is closed.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops._morph import correspond
    >>> pairs = correspond(svg.PathData("M0 0H10V10H0Z"), svg.PathData("M0 0H10V10H0ZM2 2H4V4H2Z"))
    >>> [(len(p) == len(q), closed) for p, q, closed in pairs]
    [(True, True), (True, True)]
    """
    return _correspond(a, b)


@functools.lru_cache(maxsize=64)
def _correspond(a: PathData, b: PathData) -> list[Pair]:
    first, second = _contours(a), _contours(b)
    every = [c[0] for c in first + second]
    if not every:
        return []
    stacked = np.concatenate(every)
    diagonal = float(np.hypot(*(stacked.max(axis=0) - stacked.min(axis=0)))) or 1.0
    pairs: list[Pair] = []
    for role in ("outer", "hole", "open"):
        mine, theirs = _role(first, role), _role(second, role)
        for i, j in _match(mine, theirs):
            pairs.append(_pair(mine[i] if i is not None else None, theirs[j] if j is not None else None,
                               role != "open", diagonal))
    for p, q, _ in pairs:
        p.flags.writeable = q.flags.writeable = False
    return pairs


def _contours(data: PathData) -> list[tuple[np.ndarray, bool, str]]:
    """Flattened subpaths with a role (``outer``, ``hole`` or ``open``), closed ones wound by role."""
    box = data.bbox
    size = math.hypot(box.width, box.height) if box is not None else 1.0
    raw = [(np.array(points, dtype=float), closed) for points, closed in polylines(data, MORPH_FLATNESS * (size or 1))]
    rings = [p[:-1] if closed and len(p) > 1 and np.allclose(p[0], p[-1]) else p for p, closed in raw]
    result: list[tuple[np.ndarray, bool, str]] = []
    for index, (points, (_, closed)) in enumerate(zip(rings, raw, strict=True)):
        if not closed:
            result.append((points, False, "open"))
            continue
        depth = sum(_inside(points[0], other) for k, (other, (_, shut)) in enumerate(zip(rings, raw, strict=True))
                    if k != index and shut and len(other) > 2)
        role = "hole" if depth % 2 else "outer"
        if (_area(points) < 0) == (role == "outer"):
            points = points[::-1]
        result.append((points, True, role))
    return result


def _role(contours: list[tuple[np.ndarray, bool, str]], role: str) -> list[np.ndarray]:
    return [points for points, _, kind in contours if kind == role]


def _area(points: np.ndarray) -> float:
    x, y = points[:, 0], points[:, 1]
    return float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y)) / 2


def _centroid(points: np.ndarray) -> np.ndarray:
    area = _area(points)
    if abs(area) < 1e-12:
        return np.asarray(points.mean(axis=0))
    x, y = points[:, 0], points[:, 1]
    nx, ny = np.roll(x, -1), np.roll(y, -1)
    cross = x * ny - nx * y
    return np.array([np.dot(x + nx, cross), np.dot(y + ny, cross)]) / (6 * area)


def _inside(point: np.ndarray, ring: np.ndarray) -> bool:
    x, y = point
    xs, ys = ring[:, 0], ring[:, 1]
    nx, ny = np.roll(xs, -1), np.roll(ys, -1)
    crosses = (ys > y) != (ny > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        at = xs + (y - ys) * (nx - xs) / (ny - ys)
    return bool(np.count_nonzero(crosses & (x < at)) % 2)


def _match(mine: list[np.ndarray], theirs: list[np.ndarray]) -> list[tuple[int | None, int | None]]:
    """Greedy pairing by centroid distance and size difference; leftovers pair with ``None``."""
    def describe(points: np.ndarray) -> tuple[np.ndarray, float]:
        return _centroid(points), math.sqrt(abs(_area(points)))

    left, right = [describe(p) for p in mine], [describe(p) for p in theirs]
    costs = sorted((float(np.sum((ca - cb) ** 2)) + (sa - sb) ** 2, i, j)
                   for i, (ca, sa) in enumerate(left) for j, (cb, sb) in enumerate(right))
    pairs: list[tuple[int | None, int | None]] = []
    used_left: set[int] = set()
    used_right: set[int] = set()
    for _, i, j in costs:
        if i not in used_left and j not in used_right:
            pairs.append((i, j))
            used_left.add(i)
            used_right.add(j)
    pairs += [(i, None) for i in range(len(mine)) if i not in used_left]
    pairs += [(None, j) for j in range(len(theirs)) if j not in used_right]
    return sorted(pairs, key=lambda p: (p[0] if p[0] is not None else len(mine), p[1] or 0))


def _perimeter(points: np.ndarray, closed: bool) -> float:
    ring = np.vstack([points, points[:1]]) if closed else points
    return float(np.sum(np.hypot(*np.diff(ring, axis=0).T)))


def _pair(first: np.ndarray | None, second: np.ndarray | None, closed: bool, diagonal: float) -> Pair:
    present = [p for p in (first, second) if p is not None]
    longest = max(_perimeter(p, closed) for p in present)
    count = int(np.clip(math.ceil(longest / (MORPH_SPACING * diagonal)), MORPH_MIN_POINTS, MORPH_MAX_POINTS))
    if not closed:
        count = max(2, count)
    a = _resample(first, closed, count) if first is not None else None
    b = _resample(second, closed, count) if second is not None else None
    if a is None:
        assert b is not None
        a = np.repeat(_centroid(b)[None, :] if closed else b.mean(axis=0, keepdims=True), count, axis=0)
    elif b is None:
        b = np.repeat(_centroid(a)[None, :] if closed else a.mean(axis=0, keepdims=True), count, axis=0)
    else:
        b = _align(a, b, closed)
    return a, b, closed


def _resample(points: np.ndarray, closed: bool, count: int) -> np.ndarray:
    """*count* points evenly spaced along the contour, nudged onto its sharp corners."""
    ring = np.vstack([points, points[:1]]) if closed else points
    steps = np.hypot(*np.diff(ring, axis=0).T)
    along = np.concatenate([[0.0], np.cumsum(steps)])
    total = along[-1]
    if total <= 0:
        return np.repeat(points[:1], count, axis=0)
    spots = np.linspace(0, total, count, endpoint=not closed)
    for corner in _corners(ring, closed):
        target = along[corner]
        nearest = round(target / total * (count if closed else count - 1))
        if nearest < count:
            spots[nearest] = target
    spots = np.maximum.accumulate(spots)
    return np.column_stack([np.interp(spots, along, ring[:, k]) for k in (0, 1)])


def _corners(ring: np.ndarray, closed: bool) -> list[int]:
    """Indices into *ring* where the direction turns sharply."""
    edges = np.diff(ring, axis=0)
    keep = np.hypot(*edges.T) > 0
    index = np.flatnonzero(keep)
    if len(index) < 2:
        return []
    headings = np.arctan2(edges[index, 1], edges[index, 0])
    if closed:
        turns = np.angle(np.exp(1j * (headings - np.roll(headings, 1))))
        return [int(i) for i, turn in zip(index, turns, strict=True) if abs(turn) > MORPH_CORNER]
    turns = np.angle(np.exp(1j * np.diff(headings)))
    return [int(i) for i, turn in zip(index[1:], turns, strict=True) if abs(turn) > MORPH_CORNER]


def _align(a: np.ndarray, b: np.ndarray, closed: bool) -> np.ndarray:
    """*b* started (or, when open, directed) so its points sit closest to *a*'s."""
    if not closed:
        flipped = b[::-1]
        return flipped if np.sum((flipped - a) ** 2) < np.sum((b - a) ** 2) else b
    za, zb = a[:, 0] + 1j * a[:, 1], b[:, 0] + 1j * b[:, 1]
    za, zb = za - za.mean(), zb - zb.mean()
    overlap = np.real(np.fft.ifft(np.conj(np.fft.fft(za)) * np.fft.fft(zb)))
    return np.roll(b, -int(np.argmax(overlap)), axis=0)
