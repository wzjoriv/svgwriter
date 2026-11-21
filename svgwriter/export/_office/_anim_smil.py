"""
Slide effects: the animation kinds PowerPoint and SMIL share, and reading them from SMIL elements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..._internal._timing import clock
from ._constants import COLOR_ATTRIBUTES, PATH_TOLERANCE

if TYPE_CHECKING:
    from ...elements.core import Element
    from ...transform.matrix import Matrix

__all__ = ["Effect", "smil_effect"]

Pair = tuple[float, float]


@dataclass(frozen=True)
class Effect:
    """One animation in the terms both PowerPoint and SMIL can express.

    Attributes
    ----------
    kind : str
        ``"fade_in"``, ``"fade_out"``, ``"appear"``, ``"disappear"``,
        ``"motion"``, ``"rotate"``, ``"scale"`` or ``"color"``.
    begin, dur : float
        Start and length of one play, in seconds.
    repeat : float
        Plays; ``math.inf`` for forever.
    freeze : bool
        Whether the end state stays.
    accel, decel : float
        Fractions of the duration spent speeding up and slowing down.
    reverse : bool
        Whether each play runs there and back (within `dur`).
    points : tuple of (float, float)
        Motion offsets in page units, from the shape's resting place.
    angle : float
        Rotation in degrees, clockwise.
    start, end : (float, float)
        Scale factors at the start and the end (the turning point with `reverse`).
    attribute : str
        ``"fill"`` or ``"stroke"`` for a colour change.
    color : str
        Target colour as ``#rrggbb``.

    Examples
    --------
    >>> Effect("rotate", angle=90).dur
    1.0
    """

    kind: str
    begin: float = 0.0
    dur: float = 1.0
    repeat: float = 1.0
    freeze: bool = True
    accel: float = 0.0
    decel: float = 0.0
    reverse: bool = False
    points: tuple[Pair, ...] = ()
    angle: float = 0.0
    start: Pair = (1.0, 1.0)
    end: Pair = (1.0, 1.0)
    attribute: str = "fill"
    color: str = ""


def _values(animation: Element) -> list[str]:
    values = animation.get("values")
    if values is not None:
        return [v.strip() for v in str(values).split(";") if v.strip()]
    start, stop = animation.get("from"), animation.get("to")
    return [str(v) for v in (start, stop) if v is not None]


def _numbers(value: str) -> list[float]:
    return [float(v) for v in value.replace(",", " ").split()]


def _timing(animation: Element) -> dict[str, Any] | None:
    """Begin, duration, repeats, fill and ease of *animation*, or None when not a plain clock schedule."""
    begin = clock(animation.get("begin", "0s"))
    dur = clock(animation.get("dur", "0s")) if animation.tag != "set" else 0.0
    if begin is None or dur is None:
        return None
    count = str(animation.get("repeatCount", "1"))
    accel = decel = 0.0
    splines = animation.get("keySplines")
    if splines is not None:
        x1, y1, x2, y2 = _numbers(str(splines).split(";")[0])
        accel, decel = max(0.0, x1 - y1), max(0.0, y2 - x2)
        total = accel + decel
        if total > 1:
            accel, decel = accel / total, decel / total
    return {"begin": begin, "dur": dur, "repeat": math.inf if count == "indefinite" else float(count),
            "freeze": str(animation.get("fill", "remove")) == "freeze", "accel": accel, "decel": decel}


def _page(frame: Matrix, x: float, y: float) -> Pair:
    """An offset in the animated element's frame, in page units."""
    origin, end = frame.apply(0.0, 0.0), frame.apply(x, y)
    return end.x - origin.x, end.y - origin.y


def _there_and_back(values: list[str]) -> bool:
    return len(values) == 3 and values[0] == values[2]


def _transform(animation: Element, values: list[str], frame: Matrix) -> dict[str, Any] | None:
    kind = str(animation.get("type", "translate"))
    numbers = [_numbers(v) for v in values]
    if kind == "translate":
        points = [_page(frame, p[0], p[1] if len(p) > 1 else 0.0) for p in numbers]
        return {"kind": "motion", "points": tuple(points)} if len(set(points)) > 1 else {}
    reverse = _there_and_back(values)
    last = numbers[1] if reverse else numbers[-1]
    if kind == "rotate":
        return {"kind": "rotate", "angle": last[0] - numbers[0][0], "reverse": reverse}
    if kind == "scale":
        def pair(p: list[float]) -> Pair:
            return (p[0], p[1] if len(p) > 1 else p[0])
        return {"kind": "scale", "start": pair(numbers[0]), "end": pair(last), "reverse": reverse}
    return None


def _motion(animation: Element, frame: Matrix) -> dict[str, Any] | None:
    from ..._internal._flat._flatten import polylines
    from ...pathdata.data import PathData

    path = animation.get("path")
    if path is None:
        return None
    points = [_page(frame, x, y) for line, _ in polylines(PathData(str(path)), PATH_TOLERANCE) for x, y in line]
    return {"kind": "motion", "points": tuple(points)} if len(points) > 1 else {}


def _fields(animation: Element, frame: Matrix) -> dict[str, Any] | None:
    """The kind-specific fields of an effect; ``{}`` for a pivot step with no effect of its own."""
    from ...color.color import as_color

    name = str(animation.get("attributeName", ""))
    values = _values(animation)
    if animation.tag == "animateMotion":
        return _motion(animation, frame)
    if not values:
        return None
    if animation.tag == "animateTransform":
        return _transform(animation, values, frame)
    if animation.tag == "set" and name == "visibility":
        return {"kind": "appear" if values[-1] == "visible" else "disappear"}
    if name == "opacity" and len(values) == 2:
        first, last = float(values[0]), float(values[-1])
        if (first, last) in ((0.0, 1.0), (1.0, 0.0)):
            return {"kind": "fade_in" if last else "fade_out"}
    if name in COLOR_ATTRIBUTES and animation.tag in ("animate", "animateColor"):
        reverse = _there_and_back(values)
        if len(values) == 2 or reverse:
            return {"kind": "color", "attribute": name, "color": as_color(values[1]).hex, "reverse": reverse}
    return None


def smil_effect(animation: Element, frame: Matrix) -> Effect | None:
    """The slide effect a SMIL element plays, or None when PowerPoint has no counterpart.

    Parameters
    ----------
    animation : Element
        An ``<animate>``, ``<set>``, ``<animateTransform>``, ``<animateMotion>``
        or ``<animateColor>``.
    frame : Matrix
        From the animated element's own frame to the page, for motion offsets.

    Returns
    -------
    Effect or None
        The effect; an effect of kind ``""`` for a pivot step of a scale or
        rotation (written by the presets, with no effect of its own).

    Examples
    --------
    >>> import svgwriter as svg
    >>> r = svg.rect(0, 0, 10, 10)
    >>> _ = r.animate.fade_in(2, begin=1)
    >>> effect = smil_effect(r.children[0], svg.Matrix())
    >>> effect.kind, effect.begin, effect.dur
    ('fade_in', 1.0, 2.0)
    """
    timing = _timing(animation)
    fields = _fields(animation, frame) if timing is not None else None
    if fields is None or timing is None:
        return None
    return Effect(**{"kind": "", **timing, **fields})
