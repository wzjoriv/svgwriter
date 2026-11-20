"""
Animation presets: show/hide, fades, draw-on, create/write, wipes, typewriter, slides, spins, pulses, color changes, morphs and staggers.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from .._internal._constants import (
    BLINK_VALUES,
    BOUNCE_HEIGHT,
    BOUNCE_TIMES,
    BOUNCE_VALUES,
    CONTAINERS,
    CREATE_DRAW_SHARE,
    DEFAULT_DURATION,
    FOREVER,
    FULL_TURN,
    PULSE_SCALE,
    SHAKE_DISTANCE,
    SHAKE_STEPS,
    SIDES,
    WRITE_LAG,
)
from .animation import Animate, AnimateMotion, AnimateTransform, Set

if TYPE_CHECKING:
    from .core import Element

__all__ = ["Motion"]


def _timing(dur: float, begin: float, repeat: float | str | None, freeze: bool) -> dict[str, Any]:
    timing: dict[str, Any] = {"dur": dur, "begin": begin, "fill": "freeze" if freeze else None}
    if repeat is not None:
        timing["repeat_count"] = FOREVER if repeat in (math.inf, FOREVER) else repeat
    return timing


def _longest_contour(element: Element) -> float:
    from ..ops.measure import total_length

    outline = element.local_outline()  # type: ignore[attr-defined]
    return max((total_length(part) for part in outline.subpaths()), default=0.0)


def _parts(element: Element) -> list[Element]:
    from .core import Element

    if element.tag in CONTAINERS:
        return [child for child in element.children if isinstance(child, Element)]
    return [element]


def _ink(element: Element) -> tuple[bool, float]:
    """Give *element* a stroke to draw with (its fill, or black) when it has none; return (filled, fill opacity)."""
    fill = element.get("fill")
    filled = fill is None or str(fill) != "none"
    if element.get("stroke") in (None, "none"):
        element.set("stroke", fill if filled and fill is not None else "black")
    opacity = element.get("fill-opacity")
    return filled, 1.0 if opacity is None else float(opacity)


def _create(element: Element, length: float, paint: tuple[bool, float], dur: float, begin: float, freeze: bool,
            *, reverse: bool = False) -> None:
    """Stroke drawn on (or off) by its dash offset, with the fill faded in after (or out before)."""
    filled, opacity = paint
    drawing = dur * CREATE_DRAW_SHARE if filled else dur
    dash = f"{length:.4g}"
    element.set("stroke-dasharray", f"{dash} {dash}")
    if not reverse or element.get("stroke-dashoffset") is None:
        element.set("stroke-dashoffset", 0 if reverse else dash)
    if reverse:
        stroke, fade = (0, dash, begin + dur - drawing), (opacity, 0, begin)
    else:
        stroke, fade = (dash, 0, begin), (0, opacity, begin + drawing)
        if filled:
            element.set("fill-opacity", 0)
    element.append(Animate(attribute_name="stroke-dashoffset", from_=stroke[0], to=stroke[1],
                           **_timing(drawing, stroke[2], None, freeze)))
    if filled:
        element.append(Animate(attribute_name="fill-opacity", from_=fade[0], to=fade[1],
                               **_timing(dur - drawing, fade[2], None, freeze)))


class Motion:
    """Animation presets for one element; every method adds SMIL children and returns ``self`` to chain.

    Reach it as ``element.animate``. The SMIL plays in browsers, and
    :meth:`svgwriter.Document.at`, video export and animated GIF/APNG/WebP
    play it too. Each preset takes ``dur`` (seconds), ``begin`` (seconds),
    ``repeat`` (a count, or ``"indefinite"``) and ``freeze`` (keep the end
    state; default True).

    Parameters
    ----------
    element : Element
        What to animate.

    Examples
    --------
    >>> import svgwriter as svg
    >>> dot = svg.circle(10, 10, 5, fill="red")
    >>> _ = dot.animate.fade_in(0.5).spin(2, begin=0.5)
    >>> [child.tag for child in dot.children]
    ['animate', 'animateTransform']
    """

    __slots__ = ("element",)

    def __init__(self, element: Element) -> None:
        self.element = element

    def _add(self, animation: Element) -> Motion:
        self.element.append(animation)
        return self

    def _centre(self) -> tuple[float, float]:
        box = self.element.local_bbox() if hasattr(self.element, "local_bbox") else None
        return (box.x + box.width / 2, box.y + box.height / 2) if box is not None else (0.0, 0.0)

    def tween(self, attribute: str, start: Any, end: Any, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
              repeat: float | str | None = None, freeze: bool = True) -> Motion:
        """Change any attribute from *start* to *end* (numbers, lengths, colors, lists)."""
        return self._add(Animate(attribute_name=attribute, from_=start, to=end,
                                 **_timing(dur, begin, repeat, freeze)))

    def show(self, at: float = 0.0) -> Motion:
        """Hidden until *at* seconds, then shown at once."""
        self.element.set("visibility", "hidden")
        return self._add(Set(attribute_name="visibility", to="visible", begin=at, fill="freeze"))

    def hide(self, at: float = 0.0) -> Motion:
        """Shown until *at* seconds, then hidden at once."""
        return self._add(Set(attribute_name="visibility", to="hidden", begin=at, fill="freeze"))

    def fade_in(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
                freeze: bool = True) -> Motion:
        """Opacity from 0 to 1."""
        if begin > 0:
            self.element.set("opacity", 0)
        return self.tween("opacity", 0, 1, dur, begin=begin, repeat=repeat, freeze=freeze)

    def fade_out(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
                 freeze: bool = True) -> Motion:
        """Opacity from 1 to 0."""
        return self.tween("opacity", 1, 0, dur, begin=begin, repeat=repeat, freeze=freeze)

    def draw(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
             freeze: bool = True) -> Motion:
        """Draw the stroke on from its start, as if by a pen (dash offset from full length to 0)."""
        from ..ops.measure import total_length

        length = total_length(self.element.local_outline())  # type: ignore[attr-defined]
        self.element.update(stroke_dasharray=f"{length:.4g} {length:.4g}", stroke_dashoffset=f"{length:.4g}")
        return self.tween("stroke-dashoffset", f"{length:.4g}", 0, dur, begin=begin, repeat=repeat, freeze=freeze)

    def create(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, freeze: bool = True) -> Motion:
        """Draw the outline on, then fade the fill in; a group creates every child at once.

        A shape without a stroke is drawn with its fill color. Every contour
        starts drawing together, at the same pen speed.
        """
        for part in _parts(self.element):
            _create(part, _longest_contour(part), _ink(part), dur, begin, freeze)
        return self

    def uncreate(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, freeze: bool = True) -> Motion:
        """The reverse of :meth:`create`: fade the fill out, then draw the outline off."""
        for part in _parts(self.element):
            _create(part, _longest_contour(part), _ink(part), dur, begin, freeze, reverse=True)
        return self

    def write(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, freeze: bool = True) -> Motion:
        """Create a ``<text>`` character by character (a group child by child), each starting before the last ends."""
        from .text import TSpan

        element = self.element
        if element.tag == "text":
            text = element.text_content
            if not text:
                return self
            length, paint = _longest_contour(element), _ink(element)
            element.text_content = ""
            pieces: list[tuple[Element, float, tuple[bool, float]]] = []
            for char in text:
                span = TSpan(char)
                element.append(span)
                pieces.append((span, length, paint))
        else:
            pieces = [(part, _longest_contour(part), _ink(part)) for part in _parts(element)]
        run = dur / (1 + WRITE_LAG * (len(pieces) - 1)) if pieces else dur
        for index, (piece, length, paint) in enumerate(pieces):
            _create(piece, length, paint, run, begin + index * WRITE_LAG * run, freeze)
        return self

    def wipe(self, side: str = "left", dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
             repeat: float | str | None = None, freeze: bool = True) -> Motion:
        """Reveal the element from one side (``left``, ``right``, ``top``, ``bottom``) with a growing clip."""
        from ..elements.shapes import Rect

        box = self.element.local_bbox()  # type: ignore[attr-defined]
        if box is None:
            raise TypeError(f"<{self.element.tag}> has no size to wipe")
        horizontal = side in ("left", "right")
        window = Rect(box.x, box.y, 0 if horizontal else box.width, box.height if horizontal else 0)
        size_name, full = ("width", box.width) if horizontal else ("height", box.height)
        window.append(Animate(attribute_name=size_name, from_=0, to=full, **_timing(dur, begin, repeat, freeze)))
        if side in ("right", "bottom"):
            position, start = ("x", box.x + box.width) if horizontal else ("y", box.y + box.height)
            window.set(position, start)
            window.append(Animate(attribute_name=position, from_=start, to=box.x if horizontal else box.y,
                                  **_timing(dur, begin, repeat, freeze)))
        self.element.clip(window)  # type: ignore[attr-defined]
        return self

    def typewriter(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0) -> Motion:
        """Show a ``<text>`` one character at a time over *dur* seconds."""
        from .text import TSpan

        text = self.element.text_content
        if not text:
            return self
        step = dur / len(text)
        self.element.text_content = ""
        for index, char in enumerate(text):
            span = TSpan(char, visibility="hidden")
            span.append(Set(attribute_name="visibility", to="visible", begin=begin + index * step, fill="freeze"))
            self.element.append(span)
        return self

    def _transform(self, kind: str, start: str, end: str, dur: float, begin: float, repeat: Any, freeze: bool,
                   **extra: Any) -> Motion:
        return self._add(AnimateTransform(kind, attribute_name="transform", from_=start, to=end, additive="sum",
                                          **_timing(dur, begin, repeat, freeze), **extra))

    def _about_centre(self, kind: str, values: str, dur: float, begin: float, repeat: Any, freeze: bool,
                      **extra: Any) -> Motion:
        """A scale about the element's centre: translate to it, scale, translate back (all additive)."""
        cx, cy = self._centre()
        timing = _timing(dur, begin, repeat, freeze)
        for step in (f"{cx:.4g} {cy:.4g}", None, f"{-cx:.4g} {-cy:.4g}"):
            if step is None:
                self._add(AnimateTransform(kind, attribute_name="transform", values=values, additive="sum",
                                           **timing, **extra))
            else:
                self._add(AnimateTransform("translate", attribute_name="transform", values=f"{step};{step}",
                                           additive="sum", **timing))
        return self

    def grow(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
             freeze: bool = True) -> Motion:
        """Scale up from nothing to full size about the element's centre."""
        return self._about_centre("scale", "0;1", dur, begin, repeat, freeze)

    def shrink(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
               freeze: bool = True) -> Motion:
        """Scale down from full size to nothing about the element's centre."""
        return self._about_centre("scale", "1;0", dur, begin, repeat, freeze)

    def pulse(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = FOREVER,
              scale: float = PULSE_SCALE) -> Motion:
        """Swell slightly and back, by default forever."""
        return self._about_centre("scale", f"1;{scale:g};1", dur, begin, repeat, False)

    def spin(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
             turns: float = 1.0, freeze: bool = True) -> Motion:
        """Rotate by *turns* full turns about the element's centre."""
        cx, cy = self._centre()
        return self._transform("rotate", f"0 {cx:.4g} {cy:.4g}", f"{FULL_TURN * turns:g} {cx:.4g} {cy:.4g}",
                               dur, begin, repeat, freeze)

    def slide_in(self, side: str = "left", dur: float = DEFAULT_DURATION, *, distance: float = 100.0,
                 begin: float = 0.0, repeat: float | str | None = None, freeze: bool = True) -> Motion:
        """Arrive from *distance* units toward a side (``left``, ``right``, ``top``, ``bottom``)."""
        dx, dy = SIDES[side]
        return self._transform("translate", f"{dx * distance:g} {dy * distance:g}", "0 0", dur, begin, repeat,
                               freeze)

    def move_to(self, x: float, y: float, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
                repeat: float | str | None = None, freeze: bool = True) -> Motion:
        """Glide so the element's centre ends at ``(x, y)``."""
        cx, cy = self._centre()
        return self._transform("translate", "0 0", f"{x - cx:g} {y - cy:g}", dur, begin, repeat, freeze)

    def follow(self, path: Any, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
               repeat: float | str | None = None, rotate: bool = True, freeze: bool = True) -> Motion:
        """Travel along *path* (an element or path data), turning with it when *rotate*."""
        data = path.outline() if hasattr(path, "outline") else path
        return self._add(AnimateMotion(path=str(data), rotate="auto" if rotate else None,
                                       **_timing(dur, begin, repeat, freeze)))

    def shake(self, dur: float = DEFAULT_DURATION / 2, *, begin: float = 0.0, distance: float = SHAKE_DISTANCE,
              repeat: float | str | None = None) -> Motion:
        """Jitter sideways and settle back."""
        values = ";".join(["0 0", *(f"{distance if i % 2 == 0 else -distance:g} 0" for i in range(SHAKE_STEPS)),
                           "0 0"])
        return self._add(AnimateTransform("translate", attribute_name="transform", values=values, additive="sum",
                                          **_timing(dur, begin, repeat, False)))

    def bounce(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, height: float = BOUNCE_HEIGHT,
               repeat: float | str | None = None) -> Motion:
        """Hop up and settle with smaller hops."""
        values = ";".join(f"0 {-height * v:g}" for v in BOUNCE_VALUES)
        times = ";".join(f"{t:g}" for t in BOUNCE_TIMES)
        return self._add(AnimateTransform("translate", attribute_name="transform", values=values, key_times=times,
                                          additive="sum", **_timing(dur, begin, repeat, False)))

    def blink(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
              repeat: float | str | None = FOREVER) -> Motion:
        """Switch fully off and on again, by default forever."""
        return self._add(Animate(attribute_name="opacity", values=BLINK_VALUES, calc_mode="discrete",
                                 **_timing(dur, begin, repeat, False)))

    def color_cycle(self, colors: list[Any], dur: float = DEFAULT_DURATION, *, attribute: str = "fill",
                    begin: float = 0.0, repeat: float | str | None = FOREVER) -> Motion:
        """Blend through *colors* (and back to the first), by default forever."""
        from ..color.color import as_color

        values = ";".join(as_color(c).hex for c in [*colors, colors[0]])
        return self._add(Animate(attribute_name=attribute, values=values, **_timing(dur, begin, repeat, False)))

    def morph(self, target: Element, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
              repeat: float | str | None = None, freeze: bool = True) -> Motion:
        """Turn this ``<path>``'s outline into *target*'s (any shape), matching their segments first."""
        from ..ops.interpolate import interpolate

        if self.element.tag != "path":
            raise TypeError("morph animates a <path>'s d; convert first with element.to_path()")
        start = interpolate(self.element.local_outline(), target.outline(), 0.0)  # type: ignore[attr-defined]
        end = interpolate(self.element.local_outline(), target.outline(), 1.0)  # type: ignore[attr-defined]
        self.element.set("d", start)
        return self._add(Animate(attribute_name="d", from_=str(start), to=str(end),
                                 **_timing(dur, begin, repeat, freeze)))

    def stagger(self, preset: str, step: float = 0.2, **options: Any) -> Motion:
        """Apply *preset* (a method name) to each child element, each starting *step* seconds after the last."""
        begin = float(options.pop("begin", 0.0))
        for index, child in enumerate(list(self.element)):
            getattr(Motion(child), preset)(begin=begin + index * step, **options)
        return self
