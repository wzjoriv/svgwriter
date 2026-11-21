"""
PowerPoint ``<p:timing>`` in: the effects of a slide's main sequence, with their start times from the slide's start.
"""

from __future__ import annotations

import math
import re
from typing import Any

from ._anim_smil import Effect
from ._constants import (
    A_NS,
    ACCEL_SCALE,
    ANGLE_UNIT,
    COLOR_ATTRIBUTES,
    MS_PER_SECOND,
    P_NS,
    PERCENT_SCALE,
    REPEAT_SCALE,
)

__all__ = ["read_timing"]

_PATH_POINT = re.compile(r"[MLC]\s*((?:[-+.\deE]+\s+[-+.\deE]+\s*)+)", re.IGNORECASE)
_SHAPE_ATTRIBUTES = {value: key for key, value in COLOR_ATTRIBUTES.items()}


def _p(tag: str) -> str:
    return f"{{{P_NS}}}{tag}"


def _seconds(value: str | None) -> float:
    if value is None or value == "indefinite":
        return 0.0
    return int(value) / MS_PER_SECOND


def _delay(node: Any) -> float:
    conditions = node.find(_p("stCondLst"))
    if conditions is None:
        return 0.0
    return sum(_seconds(c.get("delay")) for c in conditions.findall(_p("cond")) if c.get("evt") is None)


def _path_points(path: str, size: tuple[float, float]) -> tuple[tuple[float, float], ...]:
    points = []
    for match in _PATH_POINT.finditer(path):
        numbers = [float(v) for v in match.group(1).split()]
        points.append((numbers[-2] * size[0], numbers[-1] * size[1]))
    return tuple(points)


def _pair(node: Any, tag: str, default: tuple[float, float]) -> tuple[float, float]:
    point = node.find(_p(tag))
    if point is None:
        return default
    return int(point.get("x")) / PERCENT_SCALE, int(point.get("y")) / PERCENT_SCALE


def _fields(effect: Any, preset_class: str, size: tuple[float, float]) -> dict[str, Any] | None:
    """The kind and parameters of one effect node, from its behaviours."""
    children = effect.find(_p("childTnLst"))
    behaviours = list(children) if children is not None else []
    tags = {b.tag for b in behaviours}
    if _p("animMotion") in tags:
        motion = next(b for b in behaviours if b.tag == _p("animMotion"))
        return {"kind": "motion", "points": _path_points(motion.get("path", ""), size)}
    if _p("animRot") in tags:
        rotation = next(b for b in behaviours if b.tag == _p("animRot"))
        return {"kind": "rotate", "angle": int(rotation.get("by", "0")) / ANGLE_UNIT}
    if _p("animScale") in tags:
        scale = next(b for b in behaviours if b.tag == _p("animScale"))
        start = _pair(scale, "from", (1.0, 1.0))
        by = _pair(scale, "by", (1.0, 1.0))
        return {"kind": "scale", "start": start, "end": _pair(scale, "to", (start[0] * by[0], start[1] * by[1]))}
    if _p("animClr") in tags:
        color = next(b for b in behaviours if b.tag == _p("animClr"))
        name = color.findtext(f".//{_p('attrName')}") or "fillcolor"
        target = color.find(f"{_p('to')}/{{{A_NS}}}srgbClr")
        if target is None:
            return None
        return {"kind": "color", "attribute": _SHAPE_ATTRIBUTES.get(name, "fill"), "color": "#" + target.get("val").lower()}
    if preset_class in ("entr", "exit"):
        entering = preset_class == "entr"
        if _p("animEffect") in tags or _p("anim") in tags:
            return {"kind": "fade_in" if entering else "fade_out"}
        return {"kind": "appear" if entering else "disappear"}
    return None


def _duration(effect: Any) -> float:
    return max((_delay(t) + _seconds(t.get("dur"))) for t in effect.iter(_p("cTn")) if t is not effect) \
        if any(True for t in effect.iter(_p("cTn")) if t is not effect) else 0.0


def _effect(node: Any, begin: float, size: tuple[float, float]) -> tuple[int, Effect] | None:
    preset_class = node.get("presetClass", "")
    fields = _fields(node, preset_class, size)
    target = node.find(f".//{_p('spTgt')}")
    if fields is None or target is None:
        return None
    count = node.get("repeatCount")
    reverse = node.get("autoRev") == "1"
    dur = _duration(node)
    if fields["kind"] in ("appear", "disappear"):
        dur = 0.0
    timing = {
        "begin": begin, "dur": dur * 2 if reverse else dur, "reverse": reverse,
        "repeat": 1.0 if count is None else math.inf if count == "indefinite" else int(count) / REPEAT_SCALE,
        "freeze": node.get("fill", "hold") != "remove",
        "accel": int(node.get("accel", "0")) / ACCEL_SCALE, "decel": int(node.get("decel", "0")) / ACCEL_SCALE,
    }
    return int(target.get("spid")), Effect(**{**fields, **timing, "reverse": fields.get("reverse", reverse)})


def read_timing(slide: Any, size: tuple[float, float]) -> list[tuple[int, Effect]]:
    """The effects of a slide's main sequence, played one click after another from the slide's start.

    Parameters
    ----------
    slide : lxml element
        The ``<p:sld>`` element.
    size : (float, float)
        Slide width and height in page units, to scale motion paths.

    Returns
    -------
    list of (int, Effect)
        Shape ids and effects; click-started steps follow the previous step
        directly.

    Examples
    --------
    >>> from lxml import etree
    >>> from svgwriter.export._office._anim_smil import Effect
    >>> from svgwriter.export._office._constants import P_NS
    >>> from svgwriter.export._office._pptx_timing import timing_xml
    >>> xml = timing_xml([(4, Effect("rotate", begin=1, angle=90))], (10, 10))
    >>> slide = etree.fromstring(f'<p:sld xmlns:p="{P_NS}">{xml}</p:sld>')
    >>> read_timing(slide, (10, 10))[0][1].angle
    90.0
    """
    main = next((n for n in slide.iter(_p("cTn")) if n.get("nodeType") == "mainSeq"), None)
    if main is None:
        return []
    found: list[tuple[int, Effect]] = []
    cursor = 0.0
    for step in main.findall(f"{_p('childTnLst')}/{_p('par')}/{_p('cTn')}"):
        step_start = cursor + _delay(step)
        group_start = step_start
        for group in step.findall(f"{_p('childTnLst')}/{_p('par')}/{_p('cTn')}"):
            start = group_start + _delay(group)
            group_end = start
            for node in group.findall(f"{_p('childTnLst')}/{_p('par')}/{_p('cTn')}"):
                item = _effect(node, start + _delay(node), size)
                if item is None:
                    continue
                found.append(item)
                effect = item[1]
                length = effect.dur * (1 if math.isinf(effect.repeat) else effect.repeat)
                group_end = max(group_end, effect.begin + length)
            group_start = group_end
        cursor = group_start
    return found
