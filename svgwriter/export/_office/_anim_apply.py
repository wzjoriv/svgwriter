"""
Slide effects in: each effect as the matching ``element.animate`` preset.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from ..._internal._constants import FOREVER

if TYPE_CHECKING:
    from ...elements.core import Element
    from ._anim_smil import Effect

__all__ = ["apply_effect"]


def _timing(effect: Effect) -> dict[str, Any]:
    repeat: float | str | None = None
    if math.isinf(effect.repeat):
        repeat = FOREVER
    elif effect.repeat != 1:
        repeat = effect.repeat
    ease = (effect.accel, 0.0, 1.0 - effect.decel, 1.0) if effect.accel or effect.decel else None
    return {"begin": effect.begin, "repeat": repeat, "ease": ease}


def _local(element: Any, points: tuple[tuple[float, float], ...]) -> str:
    """Page offsets as a motion path in the element's own frame."""
    inverse = element.t.inverse()
    origin = inverse.apply(0.0, 0.0)
    local = [inverse.apply(x, y) for x, y in points]
    return "M" + " L".join(f"{p.x - origin.x:g} {p.y - origin.y:g}" for p in local)


def apply_effect(element: Element, effect: Effect) -> None:
    """Add *effect* to *element* with its ``animate`` presets.

    Parameters
    ----------
    element : Element
        A shape read from the slide.
    effect : Effect
        The effect, its motion in page units.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._office._anim_smil import Effect
    >>> r = svg.rect(0, 0, 10, 10)
    >>> apply_effect(r, Effect("fade_in", begin=1))
    >>> r.children[0].get("attributeName"), r.get("opacity")
    ('opacity', 0)
    """
    motion: Any = element.animate
    timing = _timing(effect)
    dur, kind = effect.dur, effect.kind
    if kind == "appear":
        motion.show(effect.begin)
    elif kind == "disappear":
        motion.hide(effect.begin)
    elif kind in ("fade_in", "fade_out"):
        getattr(motion, kind)(dur, freeze=effect.freeze, **timing)
    elif kind == "rotate":
        motion.rotate(effect.angle, dur, freeze=effect.freeze, **timing)
    elif kind == "motion":
        _move(motion, element, effect, timing)
    elif kind == "scale":
        _scale(motion, effect, timing)
    elif kind == "color":
        start = element.get(effect.attribute)
        if effect.reverse:
            motion.color_cycle([start, effect.color], dur, attribute=effect.attribute, **timing)
        else:
            motion.tween(effect.attribute, start, effect.color, dur, freeze=effect.freeze, **timing)


def _move(motion: Any, element: Any, effect: Effect, timing: dict[str, Any]) -> None:
    points = effect.points
    if len(points) == 2 and points[0] == (0.0, 0.0):
        motion.move_by(*points[1], effect.dur, freeze=effect.freeze, **timing)
    else:
        motion.follow(_local(element, points), effect.dur, rotate=False, freeze=effect.freeze, **timing)


def _scale(motion: Any, effect: Effect, timing: dict[str, Any]) -> None:
    (sx, sy), (ex, ey) = effect.start, effect.end
    if effect.reverse:
        motion.pulse(effect.dur, scale=ex / sx if sx else ex, **timing)
    elif sx == sy == 0:
        motion.grow(effect.dur, freeze=effect.freeze, **timing)
    elif ex == ey == 0:
        motion.shrink(effect.dur, freeze=effect.freeze, **timing)
    else:
        motion.scale((ex / sx, ey / sy), effect.dur, freeze=effect.freeze, **timing)
