"""
Animations started by a click, a hover or another pointer event instead of the clock: ``el.animate.on("click")``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..._internal._constants import DEFAULT_PRECISION, POINTER_EVENTS, SVG_EVENTS
from ..._internal._numbers import format_number

if TYPE_CHECKING:
    from ._motion import Motion
    from .core import Element

__all__ = ["EventStart", "Triggered"]


@dataclass(frozen=True)
class EventStart:
    """A SMIL ``begin`` that waits for an event on an element: ``button.click+0.5s``.

    The element's current id is read when the value is written, so it follows ids assigned later.

    Parameters
    ----------
    source : Element
        The element the event happens on.
    event : str
        The SVG event name (``"click"``, ``"mouseover"``, ...).
    offset : float, optional
        Seconds after the event. Defaults to 0.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.model.elements._motion_events import EventStart
    >>> str(EventStart(svg.rect(0, 0, 1, 1, id="key"), "click", 0.25))
    'key.click+0.25s'
    """

    source: Element
    event: str
    offset: float = 0.0

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """The ``begin`` text, such as ``key.click`` or ``key.mouseover+1s``."""
        start = f"{self.source.ensure_id()}.{self.event}"
        return f"{start}+{format_number(self.offset, precision)}s" if self.offset else start

    def __str__(self) -> str:
        return self.svg_value()


class Triggered:
    """``element.animate.on(event)``: the same presets, started by *event* instead of the clock.

    Each preset's ``begin`` becomes a delay after the event. Browsers and SVG viewers play the animation
    when the event happens; still images, PDF and video show the resting state.

    Parameters
    ----------
    motion : Motion
        The element's animation presets.
    event : str
        ``"click"``, ``"hover"``, ``"leave"``, ``"press"``, ``"release"``, ``"focus"`` or ``"blur"``, or an
        SVG 1.1 event name as written (``"mousemove"``, ``"activate"``, ``"load"``, ...).
    source : Element, optional
        The element the event happens on. Defaults to the animated element.

    Raises
    ------
    ValueError
        If *event* is not one of the names above.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(width=60, height=30)
    >>> key = doc.rect(0, 0, 20, 20, id="key")
    >>> _ = key.animate.on("click").pulse(0.3)
    >>> key.children[-1].get("begin").svg_value()
    'key.click'
    """

    __slots__ = ("event", "motion", "source")

    def __init__(self, motion: Motion, event: str, source: Element | None = None) -> None:
        if event not in POINTER_EVENTS and event not in SVG_EVENTS:
            raise ValueError(f"unknown event {event!r}; choose one of {', '.join(POINTER_EVENTS)} or an SVG 1.1 "
                             f"event ({', '.join(sorted(SVG_EVENTS))})")
        self.motion = motion
        self.event = POINTER_EVENTS.get(event, event)
        self.source = motion.element if source is None else source
        self.source.ensure_id()

    def __getattr__(self, name: str) -> Any:
        preset = getattr(self.motion, name)
        if not callable(preset):
            return preset

        def started(*args: Any, **options: Any) -> Triggered:
            before = {id(node) for node in _animations(self.motion.element)}
            preset(*args, **options)
            for node in _animations(self.motion.element):
                if id(node) not in before:
                    node.attributes["begin"] = EventStart(self.source, self.event, _seconds(node.get("begin")))
            return self

        return started

    def __dir__(self) -> list[str]:
        return dir(self.motion)


def _animations(element: Element) -> list[Element]:
    from .animation import AnimationElement

    return [node for node in element.iter() if isinstance(node, AnimationElement)]


def _seconds(begin: Any) -> float:
    """A clock ``begin`` in seconds (0 when absent or not a plain clock value)."""
    from ..._internal._animation._timing import clock

    value = clock(str(begin)) if begin is not None else 0.0
    return value if value is not None and math.isfinite(value) else 0.0
