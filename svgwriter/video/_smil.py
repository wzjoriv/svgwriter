"""
SMIL evaluation: a static copy of a document with every animation applied at one moment.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..transform.matrix import IDENTITY, Matrix
from ._constants import (
    CLOCK_RE,
    EPSILON,
    INDEFINITE,
    NUMBER_RE,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    TIME_SCALE,
    TIMECOUNT_RE,
)

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.base import Element

__all__ = ["snapshot"]


def clock(value: object) -> float | None:
    """Seconds of a SMIL clock value (``2s``, ``150ms``, ``1:30``, ``0:01:30.5``), or None."""
    text = str(value)
    match = TIMECOUNT_RE.match(text)
    if match:
        return float(match.group(1)) * TIME_SCALE[match.group(2)]
    match = CLOCK_RE.match(text)
    if match:
        hours = float(match.group(1) or 0)
        return hours * SECONDS_PER_HOUR + float(match.group(2)) * SECONDS_PER_MINUTE + float(match.group(3))
    return None


@dataclass(frozen=True)
class _Timing:
    begin: float
    dur: float | None
    active: float
    freeze: bool

    def progress(self, time: float) -> float | None:
        """Simple-time fraction in ``0..1`` at *time*, or None when the animation has no effect."""
        if time < self.begin:
            return None
        elapsed = time - self.begin
        if elapsed >= self.active:
            if not self.freeze:
                return None
            if self.dur is None or math.isinf(self.active):
                return 1.0
            remainder = (self.active / self.dur) % 1.0
            return remainder if remainder > EPSILON else 1.0
        if self.dur is None:
            return 1.0
        return (elapsed % self.dur) / self.dur


def _timing(animation: Element) -> _Timing:
    begin = clock(animation.get("begin", 0)) or 0.0
    dur = clock(animation.get("dur", "")) if str(animation.get("dur", "")) != INDEFINITE else None
    count, repeat_dur = animation.get("repeatCount"), animation.get("repeatDur")
    active = math.inf if dur is None else dur
    if count is not None:
        active = math.inf if str(count) == INDEFINITE else (dur or 0.0) * float(count)
    if repeat_dur is not None:
        limit = math.inf if str(repeat_dur) == INDEFINITE else clock(repeat_dur) or math.inf
        active = limit if count is None else min(active, limit)
    end = clock(animation.get("end", "")) if animation.get("end") is not None else None
    if end is not None:
        active = min(active, max(end - begin, 0.0))
    freeze = str(animation.get("fill", "remove")) == "freeze"
    return _Timing(begin, dur if dur else None, active, freeze)


def _values(animation: Element, base: Any) -> list[str]:
    values = animation.get("values")
    if values is not None:
        return [v.strip() for v in str(values).split(";") if v.strip()]
    start, stop, by = animation.get("from"), animation.get("to"), animation.get("by")
    first = str(start) if start is not None else ("" if base is None else str(base))
    if stop is not None:
        return [first, str(stop)]
    if by is not None:
        return [first, _add(first, str(by))]
    return [first]


def _numbers(text: str) -> list[float]:
    return [float(v) for v in NUMBER_RE.findall(text)]


def _add(a: str, b: str) -> str:
    left, right = _numbers(a), _numbers(b)
    if len(left) != len(right):
        return b
    sums = iter(x + y for x, y in zip(left, right, strict=True))
    return NUMBER_RE.sub(lambda match: f"{next(sums):g}", a)


def _segment(animation: Element, values: list[str], p: float) -> tuple[str, str, float]:
    """The two neighbouring values and the local fraction between them at progress *p*."""
    if len(values) == 1:
        return values[0], values[0], 0.0
    discrete = str(animation.get("calcMode", "linear")) == "discrete"
    times = animation.get("keyTimes")
    keys = [float(v) for v in str(times).split(";")] if times is not None else None
    if keys is None or len(keys) != len(values):
        keys = ([i / len(values) for i in range(len(values))] if discrete
                else [i / (len(values) - 1) for i in range(len(values))])
    index = max(i for i, key in enumerate(keys) if key <= p + EPSILON) if p >= keys[0] else 0
    if discrete or index >= len(values) - 1:
        return values[index], values[index], 0.0
    span = keys[index + 1] - keys[index]
    return values[index], values[index + 1], (p - keys[index]) / span if span else 0.0


def _blend(a: str, b: str, fraction: float) -> str:
    """Interpolate two attribute texts: colors, number lists (units kept), else a discrete switch."""
    from ..color.color import as_color
    from ..ops.interpolate import interpolate

    if fraction <= 0:
        return a
    try:
        return interpolate(as_color(a), as_color(b), fraction).hex  # type: ignore[no-any-return]
    except ValueError:
        pass
    left, right = _numbers(a), _numbers(b)
    if left and len(left) == len(right):
        mixed = iter(x + (y - x) * fraction for x, y in zip(left, right, strict=True))
        return NUMBER_RE.sub(lambda m: f"{next(mixed):.6g}", a)
    return a if fraction < 0.5 else b


def _target(animation: Element, root: Element) -> Element | None:
    href = animation.get("xlink:href") or animation.get("{http://www.w3.org/1999/xlink}href")
    if href:
        return root.get_element_by_id(str(href).lstrip("#"))
    return animation.parent


def _transform_matrix(kind: str, numbers: list[float]) -> Matrix:
    padded = [*numbers, 0.0, 0.0, 0.0]
    if kind == "translate":
        return Matrix.translate(padded[0], padded[1] if len(numbers) > 1 else 0.0)
    if kind == "scale":
        return Matrix.scale(padded[0], padded[1] if len(numbers) > 1 else padded[0])
    if kind == "rotate":
        return Matrix.rotate(padded[0], padded[1], padded[2])
    if kind == "skewX":
        return Matrix.skew_x(padded[0])
    if kind == "skewY":
        return Matrix.skew_y(padded[0])
    return IDENTITY


def _apply(animation: Element, target: Element, p: float, base_t: dict[int, Matrix]) -> None:
    from ..attributes.names import svg_name

    tag = animation.tag
    if tag == "animateMotion":
        _motion(animation, target, p, base_t)
        return
    name = svg_name(str(animation.get("attributeName", "")))
    if tag == "animateTransform":
        kind = str(animation.get("type", "translate"))
        a, b, fraction = _segment(animation, _values(animation, "0"), p)
        moved = _transform_matrix(kind, _numbers(_blend(a, b, fraction)))
        sum_mode = str(animation.get("additive", "replace")) == "sum"
        target.t = (target.t @ moved) if sum_mode else moved  # type: ignore[attr-defined]
        return
    base = target.get(name)
    if tag == "set":
        target.set(name, str(animation.get("to", base)))
        return
    a, b, fraction = _segment(animation, _values(animation, base), p)
    value = _blend(a, b, fraction)
    if str(animation.get("additive", "replace")) == "sum" and base is not None:
        value = _add(str(base), value)
    target.set(name, value)


def _motion(animation: Element, target: Element, p: float, base_t: dict[int, Matrix]) -> None:
    from ..ops.measure import point_at_length, tangent_at_length, total_length

    data = _motion_path(animation)
    if data is None:
        return
    length = total_length(data)
    point = point_at_length(data, p * length)
    rotate = str(animation.get("rotate", "0"))
    angle = 0.0
    if rotate in ("auto", "auto-reverse"):
        tangent = tangent_at_length(data, p * length)
        angle = math.degrees(math.atan2(tangent.y, tangent.x)) + (180.0 if rotate == "auto-reverse" else 0.0)
    elif _numbers(rotate):
        angle = _numbers(rotate)[0]
    start = base_t.setdefault(id(target), getattr(target, "t", IDENTITY))
    target.t = Matrix.translate(point.x, point.y) @ Matrix.rotate(angle) @ start  # type: ignore[attr-defined]


def _motion_path(animation: Element) -> Any:
    from ..pathdata.data import PathData

    for child in animation:
        if child.tag == "mpath":
            href = child.get("xlink:href") or child.get("{http://www.w3.org/1999/xlink}href")
            referenced = animation.root().get_element_by_id(str(href).lstrip("#")) if href else None
            if referenced is not None and hasattr(referenced, "outline"):
                return referenced.outline()
    if animation.get("path") is not None:
        return PathData(str(animation.get("path")))
    points = _values(animation, "0,0")
    pairs = [_numbers(v) for v in points]
    pairs = [pair for pair in pairs if len(pair) >= 2]
    if len(pairs) < 2:
        return None
    return PathData("M" + " L".join(f"{x:g} {y:g}" for x, y, *_ in pairs))


def snapshot(document: Document, time: float) -> Document:
    """A copy of *document* with every SMIL animation applied at *time* seconds and then removed.

    Supports ``<animate>``, ``<set>``, ``<animateColor>``, ``<animateTransform>``
    and ``<animateMotion>`` (``path``, ``values`` or ``<mpath>``, ``rotate``)
    with plain clock ``begin``/``dur``/``end``, ``repeatCount``, ``repeatDur``,
    ``fill="freeze"``, ``values``/``from``/``to``/``by``, ``keyTimes``,
    ``calcMode="discrete"`` and ``additive="sum"``. Event-based begins and
    spline timing are treated as their linear, clock-based equivalents.
    """
    from ..document import Document
    from ..elements.animation import AnimationElement

    root = document.root.clone()
    root.__dict__["_source_path"] = document.root.__dict__.get("_source_path")
    copy = Document(root=root)
    animations = list(root.find_all(AnimationElement))
    base_t: dict[int, Matrix] = {}
    for animation in animations:
        target = _target(animation, root)
        progress = _timing(animation).progress(time)
        if target is not None and progress is not None:
            _apply(animation, target, progress, base_t)
    for animation in animations:
        if animation.parent is not None:
            animation.parent.remove(animation)
    return copy
