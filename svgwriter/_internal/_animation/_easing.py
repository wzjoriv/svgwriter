"""
Cubic-bézier timing curves: evaluation, inversion and splitting, shared by SMIL writing and evaluation.
"""

from __future__ import annotations

from .._constants import EASE_BISECTIONS, EASE_NEWTON_STEPS, EPSILON

__all__ = ["spline_at", "spline_param", "spline_progress", "split_spline"]

Spline = tuple[float, float, float, float]


def _axis(a: float, b: float, s: float) -> float:
    """One coordinate of the curve from ``0`` through control values *a*, *b* to ``1`` at parameter *s*."""
    u = 1.0 - s
    return 3.0 * u * u * s * a + 3.0 * u * s * s * b + s * s * s


def _slope(a: float, b: float, s: float) -> float:
    u = 1.0 - s
    return 3.0 * u * u * a + 6.0 * u * s * (b - a) + 3.0 * s * s * (1.0 - b)


def _solve(a: float, b: float, target: float) -> float:
    """The parameter where the monotone axis through *a*, *b* reaches *target*: Newton, then bisection."""
    s = target
    for _ in range(EASE_NEWTON_STEPS):
        error = _axis(a, b, s) - target
        if abs(error) < EPSILON:
            return s
        slope = _slope(a, b, s)
        if abs(slope) < EPSILON:
            break
        s -= error / slope
        if not 0.0 <= s <= 1.0:
            break
    low, high = 0.0, 1.0
    for _ in range(EASE_BISECTIONS):
        s = (low + high) / 2
        if _axis(a, b, s) < target:
            low = s
        else:
            high = s
    return (low + high) / 2


def spline_param(spline: Spline, x: float) -> float:
    """The curve parameter at time *x* (``0..1``)."""
    return 0.0 if x <= 0 else 1.0 if x >= 1 else _solve(spline[0], spline[2], x)


def spline_at(spline: Spline, s: float) -> tuple[float, float]:
    """The point ``(time, progress)`` at curve parameter *s*."""
    return _axis(spline[0], spline[2], s), _axis(spline[1], spline[3], s)


def spline_progress(spline: Spline, x: float) -> float:
    """Progress at time *x* along the timing curve with control points *spline* (``x1, y1, x2, y2``)."""
    if x <= 0 or x >= 1:
        return 0.0 if x <= 0 else 1.0
    return _axis(spline[1], spline[3], _solve(spline[0], spline[2], x))


def split_spline(spline: Spline, start: float, stop: float) -> Spline:
    """The piece of *spline* between parameters *start* and *stop*, rescaled to the unit square."""
    xs, ys = (0.0, spline[0], spline[2], 1.0), (0.0, spline[1], spline[3], 1.0)

    def blossom(points: tuple[float, ...], u: float, v: float, w: float) -> float:
        first = [p + (q - p) * u for p, q in zip(points, points[1:], strict=False)]
        second = [p + (q - p) * v for p, q in zip(first, first[1:], strict=False)]
        return second[0] + (second[1] - second[0]) * w

    qx = [blossom(xs, *params) for params in _corners(start, stop)]
    qy = [blossom(ys, *params) for params in _corners(start, stop)]
    width, height = qx[3] - qx[0], qy[3] - qy[0]
    if width < EPSILON or height < EPSILON:
        return (0.0, 0.0, 1.0, 1.0)

    def unit(value: float) -> float:
        return min(max(round(value, 6), 0.0), 1.0)

    return (unit((qx[1] - qx[0]) / width), unit((qy[1] - qy[0]) / height),
            unit((qx[2] - qx[0]) / width), unit((qy[2] - qy[0]) / height))


def _corners(start: float, stop: float) -> tuple[tuple[float, float, float], ...]:
    return ((start, start, start), (start, start, stop), (start, stop, stop), (stop, stop, stop))
