"""
Transform animation presets: rotate, scale, skew, move, spin, grow, shrink, pulse, slide, shake and bounce.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from .._internal._constants import (
    BOUNCE_HEIGHT,
    BOUNCE_TIMES,
    BOUNCE_VALUES,
    DEFAULT_DURATION,
    FOREVER,
    FULL_TURN,
    PULSE_SCALE,
    SHAKE_DISTANCE,
    SHAKE_STEPS,
    SIDES,
)
from .._internal._numbers import format_number
from .animation import AnimateTransform, EaseLike

if TYPE_CHECKING:
    from ..transform.matrix import Point
    from ._motion import Motion
    from .core import Element

__all__ = ["TransformPresets", "timing"]

PointLike = tuple[float, float]
Pivot = PointLike | str


def _pair(x: float, y: float) -> str:
    return f"{format_number(x)} {format_number(y)}"


def timing(dur: float, begin: float, repeat: float | str | None, freeze: bool,
           ease: EaseLike | None = None) -> dict[str, Any]:
    """SMIL timing keywords shared by every preset."""
    result: dict[str, Any] = {"dur": dur, "begin": begin, "fill": "freeze" if freeze else None, "ease": ease}
    if repeat is not None:
        result["repeat_count"] = FOREVER if repeat in (math.inf, FOREVER) else repeat
    return result


class TransformPresets:
    """Presets that animate the ``transform``; mixed into :class:`~svgwriter.elements.Motion`.

    Every animation is added (``additive="sum"``) after the element's own
    transform and after earlier transform presets, so they compose: two
    ``rotate(30)`` one after the other end at 60 degrees. Pivots follow the
    static transform methods: the element's :attr:`~svgwriter.elements.Transformable.anchor`
    (its bounding-box centre unless set), ``about="bottom"`` and the other
    anchor names, or ``about=(x, y)`` in parent coordinates (local ones
    with ``local=True``).

    SMIL applies these animations in the element's own frame, after its
    transform. On an element that is only moved, rotated or scaled evenly,
    the end state equals the static method's; on one that is already
    skewed or scaled unevenly, rotations and skews follow its own axes.
    """

    __slots__ = ()

    element: Element

    def _add(self, animation: Element) -> Motion:
        raise NotImplementedError

    def _pivot(self, about: Pivot | None = None, local: bool = False) -> tuple[float, float]:
        """The pivot in the element's own coordinates, where SMIL transforms apply."""
        element: Any = self.element
        if not hasattr(element, "_pivot"):
            box = element.local_bbox() if hasattr(element, "local_bbox") else None
            return (box.x + box.width / 2, box.y + box.height / 2) if box is not None else (0.0, 0.0)
        point: Point = element._pivot(about, True)
        if about is not None and not isinstance(about, str) and not local:
            point = element.t.inverse().apply(point.x, point.y)
        return point.x, point.y

    def _vector(self, dx: float, dy: float, local: bool) -> tuple[float, float]:
        """An offset in the element's own axes; *dx*, *dy* are along the parent's unless *local*."""
        element: Any = self.element
        if local or not hasattr(element, "t"):
            return dx, dy
        inverse = element.t.inverse()
        origin, end = inverse.apply(0.0, 0.0), inverse.apply(dx, dy)
        return end.x - origin.x, end.y - origin.y

    def _transform(self, kind: str, start: str, end: str, dur: float, begin: float, repeat: Any, freeze: bool,
                   ease: EaseLike | None) -> Motion:
        return self._add(AnimateTransform(kind, attribute_name="transform", from_=start, to=end, additive="sum",
                                          **timing(dur, begin, repeat, freeze, ease)))

    def _about(self, steps: list[tuple[str, str]], pivot: tuple[float, float], dur: float, begin: float,
               repeat: Any, freeze: bool, ease: EaseLike | None) -> Motion:
        """Translate to *pivot*, run each ``(kind, values)`` step, translate back (all additive)."""
        cx, cy = pivot
        held = timing(dur, begin, repeat, freeze)
        there, back = _pair(cx, cy), _pair(-cx, -cy)
        self._add(AnimateTransform("translate", attribute_name="transform", values=f"{there};{there}",
                                   additive="sum", **held))
        for kind, values in steps:
            self._add(AnimateTransform(kind, attribute_name="transform", values=values, additive="sum",
                                       **{**held, "ease": ease}))
        return self._add(AnimateTransform("translate", attribute_name="transform", values=f"{back};{back}",
                                          additive="sum", **held))

    def rotate(self, angle: float, dur: float = DEFAULT_DURATION, *, about: Pivot | None = None,
               local: bool = False, begin: float = 0.0, repeat: float | str | None = None, freeze: bool = True,
               ease: EaseLike | None = None) -> Motion:
        """Turn by *angle* degrees from wherever the element is, about its anchor.

        Parameters
        ----------
        angle : float
            Degrees; positive turns clockwise on screen, as :meth:`Transformable.rotate`.
        dur : float, optional
            Seconds the turn takes. Defaults to 1.0.
        about : str or (float, float), optional
            Pivot: a name such as ``"bottom"`` or ``"top_left"`` (see
            :attr:`~svgwriter.elements.Transformable.anchor`), or a point in
            parent coordinates (local ones with *local*). Defaults
            to the element's anchor, so ``el.rotate(a)`` and
            ``el.animate.rotate(a)`` turn about the same point.
        local : bool, optional
            Read *about* in the element's own coordinates. Defaults to False.
        begin : float, optional
            Seconds before it starts. Defaults to 0.0.
        repeat : float or str, optional
            A count or ``"indefinite"``. Defaults to None (once).
        freeze : bool, optional
            Keep the end angle. Defaults to True.
        ease : str, tuple or callable, optional
            Timing curve (see :class:`~svgwriter.Ease`). Defaults to None (linear).

        Returns
        -------
        Motion
            The presets, for chaining.

        See Also
        --------
        spin : Whole turns.

        Notes
        -----
        SMIL adds animated transforms after the element's own, so a pivot
        given in parent coordinates is mapped into the element's frame.

        Examples
        --------
        >>> import svgwriter as svg
        >>> bar = svg.rect(0, 0, 40, 10)
        >>> _ = bar.animate.rotate(90, 2).rotate(-45, begin=2)
        >>> [a.get("to") for a in bar.children]
        ['90 20 5', '-45 20 5']
        >>> svg.rect(0, 0, 40, 10).animate.rotate(90, about="bottom_left").element.children[0].get("to")
        '90 0 10'
        """
        cx, cy = self._pivot(about, local)
        return self._transform("rotate", f"0 {_pair(cx, cy)}", f"{angle:g} {_pair(cx, cy)}", dur, begin,
                               repeat, freeze, ease)

    def scale(self, factor: float | tuple[float, float], dur: float = DEFAULT_DURATION, *,
              about: Pivot | None = None, local: bool = False, begin: float = 0.0,
              repeat: float | str | None = None, freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Scale by *factor* from the element's current size, about its anchor.

        Parameters
        ----------
        factor : float or (float, float)
            One factor for both axes, or ``(sx, sy)``; negative values mirror.
        dur : float, optional
            Seconds it takes. Defaults to 1.0.
        about : str or (float, float), optional
            Fixed point: a name or a point, as for :meth:`rotate`.
            Defaults to the element's anchor.
        local : bool, optional
            Read *about* in the element's own coordinates. Defaults to False.
        begin, repeat, freeze, ease : optional
            Timing, as for :meth:`rotate`.

        Returns
        -------
        Motion
            The presets, for chaining.

        See Also
        --------
        grow, shrink, pulse : Scaling from or to nothing, and a swell.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dot = svg.circle(50, 50, 10)
        >>> _ = dot.animate.scale(2).scale((1, 0.5), begin=1)
        >>> [a.get("values") for a in dot.children if a.get("type") == "scale"]
        ['1;2', '1 1;1 0.5']
        """
        values = f"1;{factor:g}" if isinstance(factor, int | float) else f"1 1;{factor[0]:g} {factor[1]:g}"
        return self._about([("scale", values)], self._pivot(about, local), dur, begin, repeat, freeze, ease)

    def skew(self, x: float = 0.0, y: float = 0.0, dur: float = DEFAULT_DURATION, *,
             about: Pivot | None = None, local: bool = False, begin: float = 0.0,
             repeat: float | str | None = None, freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Skew by *x* then *y* degrees from the element's current shape, about its anchor.

        Parameters
        ----------
        x, y : float, optional
            Skew angles along x and y, as :meth:`Transformable.skew`. Defaults to 0.
        dur : float, optional
            Seconds it takes. Defaults to 1.0.
        about : str or (float, float), optional
            Fixed point: a name or a point, as for :meth:`rotate`.
            Defaults to the element's anchor.
        local : bool, optional
            Read *about* in the element's own coordinates. Defaults to False.
        begin, repeat, freeze, ease : optional
            Timing, as for :meth:`rotate`.

        Returns
        -------
        Motion
            The presets, for chaining.

        Raises
        ------
        ValueError
            If both angles are 0.

        Examples
        --------
        >>> import svgwriter as svg
        >>> card = svg.rect(0, 0, 20, 10)
        >>> _ = card.animate.skew(x=30)
        >>> [a.get("type") for a in card.children]
        ['translate', 'skewX', 'translate']
        """
        steps = [(kind, f"0;{angle:g}") for kind, angle in (("skewY", y), ("skewX", x)) if angle]
        if not steps:
            raise ValueError("skew needs an angle: animate.skew(x=20) or animate.skew(y=-10)")
        return self._about(steps, self._pivot(about, local), dur, begin, repeat, freeze, ease)

    def move_by(self, dx: float, dy: float = 0.0, dur: float = DEFAULT_DURATION, *, local: bool = False,
                begin: float = 0.0, repeat: float | str | None = None, freeze: bool = True,
                ease: EaseLike | None = None) -> Motion:
        """Glide by ``(dx, dy)`` from wherever the element is.

        Parameters
        ----------
        dx, dy : float
            Offset along the parent's axes (the element's own with *local*).
            *dy* defaults to 0.
        dur : float, optional
            Seconds it takes. Defaults to 1.0.
        local : bool, optional
            Measure along the element's own (rotated, scaled) axes. Defaults to False.
        begin, repeat, freeze, ease : optional
            Timing, as for :meth:`rotate`.

        Returns
        -------
        Motion
            The presets, for chaining.

        See Also
        --------
        move_to : Glide to a point.

        Examples
        --------
        >>> import svgwriter as svg
        >>> dot = svg.circle(0, 0, 5)
        >>> dot.animate.move_by(30, 10).element.children[0].get("to")
        '30 10'
        """
        x, y = self._vector(dx, dy, local)
        return self._transform("translate", "0 0", _pair(x, y), dur, begin, repeat, freeze, ease)

    def move_to(self, x: float, y: float, dur: float = DEFAULT_DURATION, *, begin: float = 0.0,
                repeat: float | str | None = None, freeze: bool = True, ease: EaseLike | None = None) -> Motion:
        """Glide so the element's anchor (its centre unless set) ends at ``(x, y)`` in parent coordinates."""
        element: Any = self.element
        here = element.position if hasattr(element, "position") else self._pivot()
        return self.move_by(x - here[0], y - here[1], dur, begin=begin, repeat=repeat, freeze=freeze, ease=ease)

    def slide_in(self, side: str = "left", dur: float = DEFAULT_DURATION, *, distance: float = 100.0,
                 begin: float = 0.0, repeat: float | str | None = None, freeze: bool = True,
                 ease: EaseLike | None = None) -> Motion:
        """Arrive from *distance* units toward a side (``left``, ``right``, ``top``, ``bottom``)."""
        dx, dy = SIDES[side]
        return self._transform("translate", f"{dx * distance:g} {dy * distance:g}", "0 0", dur, begin, repeat,
                               freeze, ease)

    def spin(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
             turns: float = 1.0, about: Pivot | None = None, local: bool = False, freeze: bool = True,
             ease: EaseLike | None = None) -> Motion:
        """Rotate by *turns* full turns about the anchor (or *about*, as for :meth:`rotate`)."""
        return self.rotate(FULL_TURN * turns, dur, about=about, local=local, begin=begin, repeat=repeat,
                           freeze=freeze, ease=ease)

    def grow(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
             about: Pivot | None = None, local: bool = False, freeze: bool = True,
             ease: EaseLike | None = None) -> Motion:
        """Scale up from nothing to full size about the anchor (or *about*, as for :meth:`scale`)."""
        return self._about([("scale", "0;1")], self._pivot(about, local), dur, begin, repeat, freeze, ease)

    def shrink(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = None,
               about: Pivot | None = None, local: bool = False, freeze: bool = True,
               ease: EaseLike | None = None) -> Motion:
        """Scale down from full size to nothing about the anchor (or *about*, as for :meth:`scale`)."""
        return self._about([("scale", "1;0")], self._pivot(about, local), dur, begin, repeat, freeze, ease)

    def pulse(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, repeat: float | str | None = FOREVER,
              scale: float = PULSE_SCALE, about: Pivot | None = None, local: bool = False,
              ease: EaseLike | None = None) -> Motion:
        """Swell slightly and back about the anchor, by default forever."""
        return self._about([("scale", f"1;{scale:g};1")], self._pivot(about, local), dur, begin, repeat, False,
                           ease)

    def shake(self, dur: float = DEFAULT_DURATION / 2, *, begin: float = 0.0, distance: float = SHAKE_DISTANCE,
              repeat: float | str | None = None, ease: EaseLike | None = None) -> Motion:
        """Jitter sideways and settle back."""
        values = ";".join(["0 0", *(f"{distance if i % 2 == 0 else -distance:g} 0" for i in range(SHAKE_STEPS)),
                           "0 0"])
        return self._add(AnimateTransform("translate", attribute_name="transform", values=values, additive="sum",
                                          **timing(dur, begin, repeat, False, ease)))

    def bounce(self, dur: float = DEFAULT_DURATION, *, begin: float = 0.0, height: float = BOUNCE_HEIGHT,
               repeat: float | str | None = None, ease: EaseLike | None = None) -> Motion:
        """Hop up and settle with smaller hops."""
        values = ";".join(f"0 {-height * v:g}" for v in BOUNCE_VALUES)
        times = ";".join(f"{t:g}" for t in BOUNCE_TIMES)
        return self._add(AnimateTransform("translate", attribute_name="transform", values=values, key_times=times,
                                          additive="sum", **timing(dur, begin, repeat, False, ease)))
