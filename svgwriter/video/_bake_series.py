"""
Sampled values over time: keyframe simplification, number templates, colours and transform parts.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from .._internal._constants import EPSILON, NUMBER_RE
from ._constants import BAKE_DIGITS, BAKE_PLACEHOLDER, DEGREES_PER_TURN

if TYPE_CHECKING:
    from ..transform.matrix import Matrix

__all__ = ["Vector", "colors", "fill", "number", "numbers", "parts", "runs", "simplify", "template"]

Vector = tuple[float, ...]


def number(value: float) -> str:
    """*value* as short SVG text."""
    text = f"{value:.{BAKE_DIGITS}g}"
    return "0" if text == "-0" else text


def _deviation(times: Sequence[float], points: Sequence[Vector], start: int, end: int) -> tuple[float, int]:
    """The largest distance, in any component, between a point inside ``start..end`` and the straight line."""
    span = times[end] - times[start]
    worst, where = 0.0, start
    for index in range(start + 1, end):
        fraction = (times[index] - times[start]) / span if span > EPSILON else 0.0
        for a, b, p in zip(points[start], points[end], points[index], strict=True):
            distance = abs(a + (b - a) * fraction - p)
            if distance > worst:
                worst, where = distance, index
    return worst, where


def simplify(times: Sequence[float], points: Sequence[Vector], tolerance: float) -> list[int]:
    """The indices of the keyframes to keep so linear playback stays within *tolerance* of every sample.

    Ramer–Douglas–Peucker over time: a straight run keeps only its two ends.
    """
    keep = {0, len(points) - 1}
    pending = [(0, len(points) - 1)]
    while pending:
        start, end = pending.pop()
        worst, where = _deviation(times, points, start, end)
        if worst > tolerance:
            keep.add(where)
            pending += [(start, where), (where, end)]
    return sorted(keep)


def template(text: str) -> str:
    """*text* with every number replaced by a placeholder: values with the same template can interpolate."""
    return NUMBER_RE.sub(BAKE_PLACEHOLDER, text)


def numbers(text: str) -> Vector:
    return tuple(float(found) for found in NUMBER_RE.findall(text))


def fill(pattern: str, values: Vector) -> str:
    """A template with its placeholders replaced by *values*."""
    pieces = pattern.split(BAKE_PLACEHOLDER)
    return pieces[0] + "".join(number(value) + piece for value, piece in zip(values, pieces[1:], strict=True))


def runs(values: Sequence[str]) -> list[tuple[int, int]]:
    """Index ranges ``(first, last)`` of consecutive values sharing one template."""
    found: list[tuple[int, int]] = []
    start = 0
    for index in range(1, len(values) + 1):
        if index == len(values) or template(values[index]) != template(values[start]):
            found.append((start, index - 1))
            start = index
    return found


def colors(values: Sequence[str]) -> list[Vector] | None:
    """Every value as ``(r, g, b)`` in ``0..1``, or None unless all of them are plain colours."""
    from ..color.color import as_color

    found = []
    for value in values:
        try:
            color = as_color(value)
        except (ValueError, TypeError):
            return None
        found.append((color.r, color.g, color.b))
    return found


def _unwrap(angles: list[float]) -> list[float]:
    """Angles in degrees made continuous by adding whole turns."""
    result = angles[:1]
    for angle in angles[1:]:
        result.append(angle - DEGREES_PER_TURN * round((angle - result[-1]) / DEGREES_PER_TURN))
    return result


def parts(matrices: Sequence[Matrix], pivot: tuple[float, float]) -> tuple[dict[str, list[Vector]], list[int]]:
    """Each matrix as ``translate(t) translate(pivot) rotate skewX scale translate(-pivot)`` series.

    Also returns the frames no such product can express. Turning or scaling about *pivot* leaves ``t`` still.
    """
    translate, rotate, skew, scale, singular = [], [], [], [], []
    for index, matrix in enumerate(matrices):
        _, _, angle, shear, sx, sy = matrix.decompose()
        moved = matrix.apply(*pivot)
        tx, ty = moved.x - pivot[0], moved.y - pivot[1]
        if abs(sy) <= EPSILON and abs(math.cos(math.radians(angle)) * matrix.c
                                      + math.sin(math.radians(angle)) * matrix.d) > EPSILON:
            singular.append(index)
        translate.append((tx, ty))
        rotate.append(angle)
        skew.append(shear)
        scale.append((sx, sy))
    turned = _unwrap(rotate)
    return ({"translate": translate, "rotate": [(a,) for a in turned], "skewX": [(s,) for s in skew],
             "scale": scale}, singular)
