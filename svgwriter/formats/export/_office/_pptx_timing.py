"""
PowerPoint ``<p:timing>`` out: slide effects that start on their own, at their SMIL begin times.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterator
from typing import TYPE_CHECKING

from ...._internal._numbers import format_number
from ._constants import (
    A_NS,
    ACCEL_SCALE,
    ANGLE_UNIT,
    COLOR_ATTRIBUTES,
    EFFECT_PRESETS,
    MS_PER_SECOND,
    P_NS,
    PERCENT_SCALE,
    REPEAT_SCALE,
)

if TYPE_CHECKING:
    from ._anim_smil import Effect

__all__ = ["timing_xml"]

_INSTANT = 1


def _ms(seconds: float) -> int:
    return round(seconds * MS_PER_SECOND)


def _behaviour(ids: Iterator[int], spid: int, dur: int, attributes: tuple[str, ...] = (), delay: int = 0) -> str:
    names = "".join(f"<p:attrName>{name}</p:attrName>" for name in attributes)
    return (f'<p:cBhvr><p:cTn id="{next(ids)}" dur="{dur}" fill="hold"><p:stCondLst><p:cond delay="{delay}"/>'
            f'</p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            + (f"<p:attrNameLst>{names}</p:attrNameLst>" if names else "") + "</p:cBhvr>")


def _visibility(ids: Iterator[int], spid: int, value: str, delay: int = 0) -> str:
    return (f"<p:set>{_behaviour(ids, spid, _INSTANT, ('style.visibility',), delay)}"
            f'<p:to><p:strVal val="{value}"/></p:to></p:set>')


def _path(points: tuple[tuple[float, float], ...], size: tuple[float, float]) -> str:
    steps = [f"{format_number(x / size[0])} {format_number(y / size[1])}" for x, y in points]
    return "M " + " L ".join(steps) + " E"


def _behaviours(effect: Effect, ids: Iterator[int], spid: int, dur: int, size: tuple[float, float]) -> str:
    kind = effect.kind
    if kind in ("appear", "disappear"):
        return _visibility(ids, spid, "visible" if kind == "appear" else "hidden")
    if kind in ("fade_in", "fade_out"):
        if kind == "fade_in":
            shown = _visibility(ids, spid, "visible")
            return f'{shown}<p:animEffect transition="in" filter="fade">{_behaviour(ids, spid, dur)}</p:animEffect>'
        fade = f'<p:animEffect transition="out" filter="fade">{_behaviour(ids, spid, dur)}</p:animEffect>'
        return fade + _visibility(ids, spid, "hidden", max(dur - _INSTANT, 0))
    if kind == "motion":
        return (f'<p:animMotion origin="layout" path="{_path(effect.points, size)}" pathEditMode="relative">'
                f"{_behaviour(ids, spid, dur, ('ppt_x', 'ppt_y'))}</p:animMotion>")
    if kind == "rotate":
        return f'<p:animRot by="{round(effect.angle * ANGLE_UNIT)}">{_behaviour(ids, spid, dur, ("r",))}</p:animRot>'
    if kind == "scale":
        def point(tag: str, pair: tuple[float, float]) -> str:
            return f'<p:{tag} x="{round(pair[0] * PERCENT_SCALE)}" y="{round(pair[1] * PERCENT_SCALE)}"/>'
        return f"<p:animScale>{_behaviour(ids, spid, dur)}{point('from', effect.start)}{point('to', effect.end)}</p:animScale>"
    attribute = COLOR_ATTRIBUTES[effect.attribute]
    return (f'<p:animClr clrSpc="rgb" dir="cw">{_behaviour(ids, spid, dur, (attribute,))}'
            f'<p:to><a:srgbClr val="{effect.color.lstrip("#").upper()}"/></p:to></p:animClr>')


def _effect(effect: Effect, spid: int, ids: Iterator[int], first: bool, size: tuple[float, float]) -> str:
    preset_class, preset_id = EFFECT_PRESETS[effect.kind]
    dur = _ms(effect.dur / 2 if effect.reverse else effect.dur)
    extra = [f'fill="{"hold" if effect.freeze else "remove"}"']
    if effect.repeat != 1:
        extra.append(f'repeatCount="{"indefinite" if math.isinf(effect.repeat) else round(effect.repeat * REPEAT_SCALE)}"')
    if effect.accel:
        extra.append(f'accel="{round(effect.accel * ACCEL_SCALE)}"')
    if effect.decel:
        extra.append(f'decel="{round(effect.decel * ACCEL_SCALE)}"')
    if effect.reverse:
        extra.append('autoRev="1"')
    node = "afterEffect" if first else "withEffect"
    head = (f'<p:par><p:cTn id="{next(ids)}" presetID="{preset_id}" presetClass="{preset_class}" presetSubtype="0" '
            f'{" ".join(extra)} nodeType="{node}"><p:stCondLst><p:cond delay="{_ms(effect.begin)}"/></p:stCondLst>')
    return f"{head}<p:childTnLst>{_behaviours(effect, ids, spid, dur, size)}</p:childTnLst></p:cTn></p:par>"


def _sequence(effects: list[tuple[int, Effect]], ids: Iterator[int], size: tuple[float, float]) -> str:
    """The effects of one sequence, each after its own delay, as one group of a click."""
    effects = sorted(effects, key=lambda pair: pair[1].begin)
    return "".join(_effect(effect, spid, ids, index == 0, size) for index, (spid, effect) in enumerate(effects))


def _interactive(trigger: int, effects: list[tuple[int, Effect]], ids: Iterator[int], size: tuple[float, float]) -> str:
    """A trigger sequence: the effects play each time shape *trigger* is clicked in the slide show."""
    target = f'<p:tgtEl><p:spTgt spid="{trigger}"/></p:tgtEl>'
    sequence, group = next(ids), next(ids)
    body = _sequence(effects, ids, size).replace('nodeType="afterEffect"', 'nodeType="clickEffect"', 1)
    return (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{sequence}" restart="whenNotActive" fill="hold" '
            f'evtFilter="cancelBubble" nodeType="interactiveSeq"><p:stCondLst><p:cond evt="onClick" delay="0">'
            f'{target}</p:cond></p:stCondLst><p:endSync evt="end" delay="0"><p:rtn val="all"/></p:endSync>'
            f'<p:childTnLst><p:par><p:cTn id="{group}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f"<p:childTnLst>{body}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>"
            f'<p:nextCondLst><p:cond evt="onClick" delay="0">{target}</p:cond></p:nextCondLst></p:seq>')


def timing_xml(effects: list[tuple[int, Effect]], size: tuple[float, float],
               triggers: dict[str, int] | None = None) -> str:
    """The ``<p:timing>`` of a slide: effects that start with the slide, and effects started by a click.

    Effects with a :attr:`~Effect.trigger` play each time that shape is clicked in the slide show (a
    PowerPoint trigger); the others start with the slide, each after its own delay.

    Parameters
    ----------
    effects : list of (int, Effect)
        Shape ids and the effects to play on them.
    size : (float, float)
        Slide width and height in page units, for motion paths (written as
        fractions of the slide).
    triggers : dict of str to int, optional
        The shape id of each trigger element, by element id. Defaults to None (no triggers);
        effects whose trigger has no shape are left out.

    Returns
    -------
    str
        The element, with the PresentationML and DrawingML namespaces declared.

    Examples
    --------
    >>> from svgwriter.formats.export._office._anim_smil import Effect
    >>> xml = timing_xml([(2, Effect("fade_in", begin=0.5))], (100, 100))
    >>> 'presetClass="entr"' in xml and '<p:cond delay="500"/>' in xml
    True
    >>> xml = timing_xml([(2, Effect("fade_in", trigger="key"))], (100, 100), {"key": 3})
    >>> 'nodeType="interactiveSeq"' in xml and '<p:spTgt spid="3"/>' in xml
    True
    """
    triggers = triggers or {}
    ids = itertools.count(1)
    timed = [(spid, effect) for spid, effect in effects if not effect.trigger]
    clicked: dict[int, list[tuple[int, Effect]]] = {}
    for spid, effect in effects:
        if effect.trigger and effect.trigger in triggers:
            clicked.setdefault(triggers[effect.trigger], []).append((spid, effect))
    root = next(ids)
    sequences = []
    if timed:
        main, click, group = next(ids), next(ids), next(ids)
        slide_target = "<p:tgtEl><p:sldTgt/></p:tgtEl>"
        sequences.append(
            f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{main}" dur="indefinite" nodeType="mainSeq">'
            f'<p:childTnLst><p:par><p:cTn id="{click}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
            f'<p:cond evt="onBegin" delay="0"><p:tn val="{main}"/></p:cond></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{group}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f"<p:childTnLst>{_sequence(timed, ids, size)}</p:childTnLst></p:cTn></p:par>"
            f"</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>"
            f'<p:prevCondLst><p:cond evt="onPrev" delay="0">{slide_target}</p:cond></p:prevCondLst>'
            f'<p:nextCondLst><p:cond evt="onNext" delay="0">{slide_target}</p:cond></p:nextCondLst></p:seq>')
    sequences += [_interactive(trigger, found, ids, size) for trigger, found in clicked.items()]
    return (f'<p:timing xmlns:p="{P_NS}" xmlns:a="{A_NS}"><p:tnLst><p:par>'
            f'<p:cTn id="{root}" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            f'{"".join(sequences)}</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
