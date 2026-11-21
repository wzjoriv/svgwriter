"""
SMIL timing: clock values, begin and end lists with sync bases, and the active interval at one moment.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .._constants import (
    CLOCK_RE,
    EPSILON,
    INDEFINITE,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    SYNC_DEPTH,
    SYNCBASE_RE,
    TIME_SCALE,
    TIMECOUNT_RE,
)

if TYPE_CHECKING:
    from ...model.elements.core import Element

__all__ = ["Timing", "clock", "timing"]


def clock(value: object) -> float | None:
    """Seconds of a SMIL clock value (``2s``, ``150ms``, ``1:30``, ``0:01:30.5``), or None.

    Examples
    --------
    >>> clock("150ms"), clock("1:30"), clock("click")
    (0.15, 90.0, None)
    """
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
class Timing:
    """One interval of an animation: when it begins, its simple duration and active length, and its fill."""

    begin: float
    dur: float | None
    active: float
    freeze: bool

    def progress(self, time: float) -> float | None:
        """Simple-time fraction in ``0..1`` at *time*, or None when the animation has no effect.

        Examples
        --------
        >>> Timing(1.0, 2.0, 2.0, False).progress(2.0)
        0.5
        >>> Timing(1.0, 2.0, 2.0, False).progress(4.0) is None
        True
        """
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


def timing(animation: Element, time: float, depth: int = 0) -> Timing:
    """The interval of *animation* that governs *time*: the latest begin at or before it.

    ``begin`` and ``end`` are lists of clock values and sync bases (``other.begin + 1s``,
    ``other.end``). Event, access-key and ``indefinite`` times never occur in a static
    document, so an animation that only has those never starts.

    Parameters
    ----------
    animation : Element
        An animation element inside its document.
    time : float
        The document time in seconds.
    depth : int, optional
        How many sync bases led here (guards cycles). Defaults to 0.

    Returns
    -------
    Timing
        The governing interval; its ``begin`` is infinite when none has started.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document.from_string(
    ...     '<svg xmlns="http://www.w3.org/2000/svg"><rect><set id="a" attributeName="x" to="1" '
    ...     'begin="1s" dur="2s"/><set attributeName="y" to="1" begin="a.end+1s; click"/></rect></svg>')
    >>> first, second = doc.root.iter("set")
    >>> timing(second, 10.0).begin
    4.0
    """
    begins = _instants(animation, "begin", depth) if animation.get("begin") is not None else [0.0]
    started = [b for b in begins if b <= time + EPSILON]
    begin = max(started) if started else min(begins, default=math.inf)
    raw_dur = str(animation.get("dur", ""))
    dur = clock(raw_dur) if raw_dur != INDEFINITE else None
    count, repeat_dur = animation.get("repeatCount"), animation.get("repeatDur")
    active = math.inf if dur is None else dur
    if count is not None:
        active = math.inf if str(count) == INDEFINITE else (dur or 0.0) * float(count)
    if repeat_dur is not None:
        limit = math.inf if str(repeat_dur) == INDEFINITE else clock(repeat_dur) or math.inf
        active = limit if count is None else min(active, limit)
    if animation.get("end") is not None and math.isfinite(begin):
        ends = [e for e in _instants(animation, "end", depth) if e >= begin]
        if ends:
            active = min(active, min(ends) - begin)
    freeze = str(animation.get("fill", "remove")) == "freeze"
    return Timing(begin, dur if dur else None, active, freeze)


def _instants(animation: Element, name: str, depth: int) -> list[float]:
    times = []
    for token in str(animation.get(name)).split(";"):
        token = token.strip()
        value = clock(token)
        if value is not None:
            times.append(value)
            continue
        match = SYNCBASE_RE.match(token)
        if match is None or depth >= SYNC_DEPTH:
            continue
        base = animation.root().get_element_by_id(match.group(1))
        if base is None:
            continue
        offset = clock(match.group(4).replace(" ", "")) if match.group(4) else 0.0
        interval = timing(base, math.inf, depth + 1)
        moment = interval.begin if match.group(2) == "begin" else interval.begin + interval.active
        if offset is not None and math.isfinite(moment):
            times.append(moment + (-offset if match.group(3) == "-" else offset))
    return times
