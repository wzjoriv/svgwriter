"""
Animation presets: show/hide, fades, draw-on, create/write, wipes, typewriter, color changes, morphs, staggers, and the transform presets.
"""

from __future__ import annotations

import difflib
import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Concatenate

from .._internal._constants import (
    BLINK_VALUES,
    CONTAINERS,
    CREATE_DRAW_SHARE,
    DEFAULT_DURATION,
    FOREVER,
    MOTION_HELPERS,
    SUGGESTIONS,
    WRITE_LAG,
)
from .._internal._presets import ANIMATIONS, BEHAVIORS
from .._internal._scenes import scene_of
from .._internal._typing import P
from ._motion_transform import TransformPresets, timing
from .animation import Animate, AnimateMotion, Ease, EaseLike, Set

if TYPE_CHECKING:
    from .core import Element

__all__ = ["Motion"]


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
            *, reverse: bool = False, ease: EaseLike | None = None) -> None:
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
                           **timing(drawing, stroke[2], None, freeze, ease)))
    if filled:
        element.append(Animate(attribute_name="fill-opacity", from_=fade[0], to=fade[1],
                               **timing(dur - drawing, fade[2], None, freeze, ease)))


class Motion(TransformPresets):
    """Animation presets for one element; every method adds SMIL children and returns ``self`` to chain.

    Reach it as ``element.animate``. The SMIL plays in browsers, and
    :meth:`svgwriter.Document.at`, video export and animated GIF/APNG/WebP
    play it too. Each preset takes ``dur`` (seconds), ``begin`` (seconds),
    ``repeat`` (a count, or ``"indefinite"``), ``freeze`` (keep the end
    state; default True) and ``ease``, a timing curve over the whole preset
    (a name such as ``"ease-in-out"``, a bézier 4-tuple, ``("steps", n)`` or
    a function; see :class:`~svgwriter.Ease`). ``show`` and ``hide`` act at
    one instant, so they take only the moment. Presets added with
    :func:`@svg.preset.animation <svgwriter.preset.animation>` are methods too, and so are behaviors
    (:func:`@svg.preset.behavior <svgwriter.preset.behavior>`), which attach to the scene owning the element.

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
    >>> _ = dot.animate.move_to(80, 10, ease="ease-in-out")
    >>> dot.children[-1].get("keySplines")
    '0.42 0 0.58 1'
    """

    __slots__ = ("element",)

    def __init__(self, element: Element) -> None:
        self.element = element

    def _add(self, animation: Element) -> Motion:
        self.element.append(animation)
        return self

    def __getattribute__(self, name: str) -> Any:
        function = ANIMATIONS.user.get(name)
        if function is None:
            return object.__getattribute__(self, name)

        @functools.wraps(function)
        def preset(*args: Any, **options: Any) -> Motion:
            return self.apply(function, *args, **options)

        return preset

    def __getattr__(self, name: str) -> Any:
        if name in BEHAVIORS:
            return self._attach(name)
        close = difflib.get_close_matches(name, [*ANIMATIONS.names(), *BEHAVIORS.names()], n=SUGGESTIONS)
        hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
        raise AttributeError(f"no animation preset or behavior {name!r}{hint} (@svg.preset.animation or "
                             "@svg.preset.behavior adds one)", name=name, obj=self)

    def __dir__(self) -> list[str]:
        return sorted({*super().__dir__(), *ANIMATIONS, *BEHAVIORS})

    def _attach(self, name: str) -> Callable[..., Motion]:
        """``element.animate.<behavior>(**options)``: attach the behavior to the scene owning the element."""
        function = BEHAVIORS.get(name)

        @functools.wraps(function)
        def attach(**options: Any) -> Motion:
            scene = scene_of(self.element)
            if scene is None:
                raise ValueError(f"behavior {name!r} runs in a scene: add the <{self.element.tag}> to a Scene's "
                                 "document first, or call scene.attach(element, function)")
            scene.attach(self.element, function, **options)
            return self

        return attach

    def apply(self, function: Callable[Concatenate[Motion, P], Motion | None], *args: P.args,
              **kwargs: P.kwargs) -> Motion:
        """Run an animation function on this element: ``function(self, *args, **kwargs)``.

        Typed with the function's own parameters, so editors complete and check its options. The
        function need not be registered; :func:`@svg.preset.animation <svgwriter.preset.animation>` also makes it
        ``element.animate.<name>``.

        Parameters
        ----------
        function : callable
            ``function(motion, *, option=default, ...)`` returning the motion or None.
        *args, **kwargs
            Passed on to *function*.

        Returns
        -------
        Motion
            This motion, to chain further presets.

        Examples
        --------
        >>> import svgwriter as svg
        >>> def lift(motion: svg.Motion, *, height: float = 8) -> svg.Motion:
        ...     return motion.move_by(0, -height)
        >>> dot = svg.circle(0, 0, 2)
        >>> dot.animate.apply(lift, height=3).fade_in().element is dot
        True
        """
        function(self, *args, **kwargs)
        return self

    def tween(self, attribute: str, start: Any, end: Any, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
              repeat: float | str | None = None, freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Change any attribute from *start* to *end* (numbers, lengths, colors, lists)."""
        return self._add(Animate(attribute_name=attribute, from_=start, to=end,
                                 **timing(dur, begin, repeat, freeze, ease)))

    def show(self, at: float = 0.0) -> Motion:
        """Hidden until *at* seconds, then shown at once."""
        self.element.set("visibility", "hidden")
        return self._add(Set(attribute_name="visibility", to="visible", begin=at, fill="freeze"))

    def hide(self, at: float = 0.0) -> Motion:
        """Shown until *at* seconds, then hidden at once."""
        return self._add(Set(attribute_name="visibility", to="hidden", begin=at, fill="freeze"))

    def fade_in(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
                freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Opacity from 0 to 1."""
        if begin > 0:
            self.element.set("opacity", 0)
        return self.tween("opacity", 0, 1, dur, begin=begin, repeat=repeat, freeze=freeze,
                          ease=ease)

    def fade_out(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
                 freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Opacity from 1 to 0."""
        return self.tween("opacity", 1, 0, dur, begin=begin, repeat=repeat, freeze=freeze,
                          ease=ease)

    def draw(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
             freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Draw the stroke on from its start, as if by a pen (dash offset from full length to 0)."""
        from ..ops.measure import total_length

        length = total_length(self.element.local_outline())  # type: ignore[attr-defined]
        self.element.update(stroke_dasharray=f"{length:.4g} {length:.4g}", stroke_dashoffset=f"{length:.4g}")
        return self.tween("stroke-dashoffset", f"{length:.4g}", 0, dur, begin=begin, repeat=repeat, freeze=freeze,
                          ease=ease)

    def create(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, freeze: bool = True,
               ease: EaseLike | None = None) -> Motion:
        """Draw the outline on, then fade the fill in; a group creates every child at once.

        A shape without a stroke is drawn with its fill color. Every contour
        starts drawing together, at the same pen speed. *ease* shapes the
        drawing and the fade each.
        """
        for part in _parts(self.element):
            _create(part, _longest_contour(part), _ink(part), dur, begin, freeze, ease=ease)
        return self

    def uncreate(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, freeze: bool = True,
                 ease: EaseLike | None = None) -> Motion:
        """The reverse of :meth:`create`: fade the fill out, then draw the outline off."""
        for part in _parts(self.element):
            _create(part, _longest_contour(part), _ink(part), dur, begin, freeze, reverse=True, ease=ease)
        return self

    def write(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, freeze: bool = True,
              ease: EaseLike | None = None) -> Motion:
        """Create a ``<text>`` character by character (a group child by child), each starting before the last ends.

        *ease* spaces the starts along the curve and shapes each character's drawing.
        """
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
        curve = Ease("linear" if ease is None else ease)
        for index, (piece, length, paint) in enumerate(pieces):
            start = begin + (dur - run) * curve.time_of(index * WRITE_LAG * run / (dur - run)) if dur > run else begin
            _create(piece, length, paint, run, start, freeze, ease=ease)
        return self

    def wipe(self, side: str = "left", dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
             repeat: float | str | None = None, freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Reveal the element from one side (``left``, ``right``, ``top``, ``bottom``) with a growing clip."""
        from .shapes import Rect

        box = self.element.local_bbox()  # type: ignore[attr-defined]
        if box is None:
            raise TypeError(f"<{self.element.tag}> has no size to wipe")
        horizontal = side in ("left", "right")
        window = Rect(box.x, box.y, 0 if horizontal else box.width, box.height if horizontal else 0)
        size_name, full = ("width", box.width) if horizontal else ("height", box.height)
        window.append(Animate(attribute_name=size_name, from_=0, to=full,
                              **timing(dur, begin, repeat, freeze, ease)))
        if side in ("right", "bottom"):
            position, start = ("x", box.x + box.width) if horizontal else ("y", box.y + box.height)
            window.set(position, start)
            window.append(Animate(attribute_name=position, from_=start, to=box.x if horizontal else box.y,
                                  **timing(dur, begin, repeat, freeze, ease)))
        self.element.clip(window)  # type: ignore[attr-defined]
        return self

    def typewriter(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
                   ease: EaseLike | None = None) -> Motion:
        """Show a ``<text>`` one character at a time over *dur* seconds (*ease* spaces the characters)."""
        from .text import TSpan

        text = self.element.text_content
        if not text:
            return self
        curve = Ease("linear" if ease is None else ease)
        self.element.text_content = ""
        for index, char in enumerate(text):
            span = TSpan(char, visibility="hidden")
            shown = begin + dur * curve.time_of(index / len(text))
            span.append(Set(attribute_name="visibility", to="visible", begin=shown, fill="freeze"))
            self.element.append(span)
        return self

    def follow(self, path: Any, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
               repeat: float | str | None = None, rotate: bool = True, freeze: bool = True,
               ease: EaseLike | None = None) -> Motion:
        """Travel along *path* (an element or path data), turning with it when *rotate*."""
        data = path.outline() if hasattr(path, "outline") else path
        return self._add(AnimateMotion(path=str(data), rotate="auto" if rotate else None,
                                       **timing(dur, begin, repeat, freeze, ease)))

    def blink(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
              repeat: float | str | None = FOREVER, ease: EaseLike | None = None) -> Motion:
        """Switch fully off and on again, by default forever."""
        return self._add(Animate(attribute_name="opacity", values=BLINK_VALUES, calc_mode="discrete",
                                 **timing(dur, begin, repeat, False, ease)))

    def color_cycle(self, colors: list[Any], dur: float = DEFAULT_DURATION, *, attribute: str = "fill",
                    begin: float = 0.0, repeat: float | str | None = FOREVER,
                    ease: EaseLike | None = None) -> Motion:
        """Blend through *colors* (and back to the first), by default forever."""
        from ..color.color import as_color

        values = ";".join(as_color(c).hex for c in [*colors, colors[0]])
        return self._add(Animate(attribute_name=attribute, values=values,
                                 **timing(dur, begin, repeat, False, ease)))

    def morph(self, target: Element, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
              repeat: float | str | None = None, freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Turn this ``<path>``'s outline into *target*'s, matching their segments first.

        Both outlines are brought to the same commands and segment count, so
        the ``d`` attribute can be interpolated; the path's own ``d`` is
        rewritten to the matched start shape, which looks the same.

        Parameters
        ----------
        target : Element
            Any shape with an outline (``<rect>``, ``<circle>``, ``<path>``...).
        dur : float, optional
            Seconds the morph takes. Defaults to 1.0.
        begin : float, optional
            Seconds before it starts. Defaults to 0.0.
        repeat : float or str, optional
            ``repeatCount``: a number or ``"indefinite"``. Defaults to None (once).
        freeze : bool, optional
            Keep the target shape after the end. Defaults to True.
        ease : str or callable, optional
            Easing name or curve. Defaults to None (linear).

        Returns
        -------
        Motion
            This object, for chaining.

        Raises
        ------
        TypeError
            If the element is not a ``<path>``; convert it with ``to_path()`` first.

        See Also
        --------
        svgwriter.interpolate : The segment matching and blending used here.

        Examples
        --------
        >>> import svgwriter as svg
        >>> shape = svg.rect(0, 0, 20, 20).to_path()
        >>> _ = shape.animate.morph(svg.circle(10, 10, 10), 2)
        >>> anim = shape.find(svg.Animate)
        >>> anim.get("attributeName"), anim.get("dur")
        ('d', '2s')
        >>> svg.circle(0, 0, 1).animate.morph(shape)
        Traceback (most recent call last):
        ...
        TypeError: morph animates a <path>'s d; convert first with element.to_path()
        """
        from ..ops.interpolate import interpolate

        if self.element.tag != "path":
            raise TypeError("morph animates a <path>'s d; convert first with element.to_path()")
        start = interpolate(self.element.local_outline(), target.outline(), 0.0)  # type: ignore[attr-defined]
        end = interpolate(self.element.local_outline(), target.outline(), 1.0)  # type: ignore[attr-defined]
        self.element.set("d", start)
        return self._add(Animate(attribute_name="d", from_=str(start), to=str(end),
                                 **timing(dur, begin, repeat, freeze, ease)))

    def stagger(self, preset: str, step: float = 0.2, **options: Any) -> Motion:
        """Apply *preset* (a method name) to each child element, each starting *step* seconds after the last."""
        begin = float(options.pop("begin", 0.0))
        for index, child in enumerate(list(self.element)):
            getattr(Motion(child), preset)(begin=begin + index * step, **options)
        return self


for _name, _member in vars(Motion).items():
    if not _name.startswith("_") and _name not in MOTION_HELPERS and callable(_member):
        ANIMATIONS.add_builtin(_name, _member)
for _name, _member in vars(TransformPresets).items():
    if not _name.startswith("_") and callable(_member):
        ANIMATIONS.add_builtin(_name, _member)
