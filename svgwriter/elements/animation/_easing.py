"""
Timing curves (``ease=``): named and cubic-bézier curves, steps and Python functions, written as SMIL timing.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

from ..._internal._animation._easing import spline_at, spline_param, spline_progress, split_spline
from ..._internal._animation._smil import add_values, blend
from ..._internal._constants import (
    EASE_BEND_SAMPLES,
    EASE_BISECTIONS,
    EASE_CURVES,
    EASE_GRID,
    EASE_SAMPLES,
    EPSILON,
)

if TYPE_CHECKING:
    from ..core import Element

__all__ = ["Ease", "EaseLike", "apply_ease"]

def _keys(count: int, key_times: Sequence[float] | None, discrete: bool) -> list[float]:
    if key_times is not None and len(key_times) == count:
        return [float(k) for k in key_times]
    if discrete or count == 1:
        return [i / count for i in range(count)]
    return [i / (count - 1) for i in range(count)]


def _value_at(values: Sequence[str], keys: Sequence[float], progress: float) -> str:
    """The value at *progress* through *values* placed at *keys*, extrapolating past either end."""
    if len(values) == 1:
        return values[0]
    index = 0
    while index < len(values) - 2 and progress > keys[index + 1]:
        index += 1
    span = keys[index + 1] - keys[index]
    return blend(values[index], values[index + 1], (progress - keys[index]) / span if span else 1.0)


def _number(value: float) -> float:
    return round(value, 6) + 0.0


class Ease:
    """A timing curve: how an animation's progress runs over its duration.

    Every animation element and every ``element.animate`` preset takes one as
    ``ease=``, in any of the forms below, and the curve applies to the whole
    timeline: with several ``values`` the motion through all of them follows
    the one curve (``keyTimes`` are moved accordingly). Bézier curves are
    written as SMIL ``calcMode="spline"`` with exact ``keySplines``; steps as
    ``calcMode="discrete"``; a Python function is sampled into ``values``
    with ``keyTimes`` at 24 to 60 evenly spaced times, more the more the
    curve bends, and played linearly between them.

    Parameters
    ----------
    curve : str, tuple, callable or Ease, optional
        One of

        - a name: ``"linear"`` (the default), ``"ease"``, ``"ease-in"``,
          ``"ease-out"``, ``"ease-in-out"`` (the standard cubic-bézier
          curves), ``"step-start"`` or ``"step-end"``;
        - ``(x1, y1, x2, y2)``: a cubic bézier from ``(0, 0)`` to ``(1, 1)``
          with ``0 <= x1, x2 <= 1``; ``y`` beyond ``0..1`` overshoots (and is
          then sampled, since SMIL splines stay inside the unit square);
        - ``("steps", n)`` or ``("steps", n, "start")``: *n* equal jumps,
          at the end (default) or the start of each interval;
        - a function from time ``0..1`` to progress, normally ``0..1`` but
          free to overshoot (``f(0)`` should be 0 and ``f(1)`` 1);
        - another ``Ease``.

    Raises
    ------
    ValueError
        For an unknown name, a bézier ``x`` outside ``0..1`` or a step count
        below 1.
    TypeError
        For anything else.

    See Also
    --------
    Animate : Takes ``ease``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.Ease("ease-in")(0.5) < 0.5
    True
    >>> slide = svg.Animate(attribute_name="x", from_=0, to=100, dur=1, ease="ease-out")
    >>> slide.get("keySplines"), slide.get("calcMode")
    ('0 0 0.58 1', 'spline')
    >>> svg.Ease(("steps", 4))(0.6)
    0.5
    >>> svg.Ease(lambda t: t * t)(0.5)
    0.25

    Notes
    -----
    Progress at time ``x`` along a bézier is found by solving ``x(s) = x``
    for the curve parameter with Newton's method, falling back to bisection,
    the same way the SMIL evaluator behind ``doc.at`` plays ``keySplines``.
    """

    __slots__ = ("_function", "_label", "_spline", "_steps")

    def __init__(self, curve: EaseLike = "linear") -> None:
        self._spline: tuple[float, float, float, float] | None = None
        self._steps: tuple[int, bool] | None = None
        self._function: Callable[[float], float] | None = None
        self._label = repr(curve)
        if isinstance(curve, Ease):
            self._spline, self._steps, self._function, self._label = (curve._spline, curve._steps,
                                                                      curve._function, curve._label)
        elif isinstance(curve, str):
            self._named(curve)
        elif isinstance(curve, tuple) and curve and curve[0] == "steps":
            self._stepped(curve)
        elif isinstance(curve, (tuple, list)) and len(curve) == 4:
            x1, y1, x2, y2 = (float(v) for v in curve)
            if not (0.0 <= x1 <= 1.0 and 0.0 <= x2 <= 1.0):
                raise ValueError(f"bézier ease x values must lie in 0..1, got {tuple(curve)}")
            self._spline = (x1, y1, x2, y2)
            self._label = f"({x1:g}, {y1:g}, {x2:g}, {y2:g})"
        elif callable(curve):
            self._function = curve
            self._label = getattr(curve, "__name__", "function")
        else:
            raise TypeError(f"not an ease: {curve!r}")

    def _named(self, name: str) -> None:
        self._label = repr(name)
        if name in EASE_CURVES:
            self._spline = EASE_CURVES[name]
        elif name in ("step-start", "step-end"):
            self._steps = (1, name == "step-start")
        else:
            raise ValueError(f"unknown ease {name!r}; use one of {[*EASE_CURVES, 'step-start', 'step-end']}")

    def _stepped(self, curve: tuple[Any, ...]) -> None:
        count = int(curve[1]) if len(curve) > 1 else 0
        position = curve[2] if len(curve) > 2 else "end"
        if count < 1 or position not in ("start", "end") or len(curve) > 3:
            raise ValueError(f"steps ease is ('steps', n) or ('steps', n, 'start'|'end') with n >= 1, got {curve!r}")
        self._steps = (count, position == "start")
        self._label = repr(curve)

    def __repr__(self) -> str:
        return f"Ease({self._label})"

    @property
    def linear(self) -> bool:
        """Whether the curve is the identity, so it changes nothing."""
        return self._spline == EASE_CURVES["linear"]

    def __call__(self, t: float) -> float:
        """Progress at time *t* (both ``0..1``)."""
        t = min(max(t, 0.0), 1.0)
        if self._function is not None:
            return float(self._function(t))
        if self._steps is not None:
            count, start = self._steps
            return min(math.floor(t * count) + (1 if start else 0), count) / count
        assert self._spline is not None
        return spline_progress(self._spline, t)

    def time_of(self, progress: float) -> float:
        """The earliest time (``0..1``) at which the curve reaches *progress*.

        Parameters
        ----------
        progress : float
            Target progress.

        Returns
        -------
        float
            The time, or 1.0 when the curve never gets there.

        Examples
        --------
        >>> round(Ease("ease-in").time_of(0.5), 3)
        0.657
        """
        if progress <= self(0.0) + EPSILON:
            return 0.0
        if self._steps is not None:
            count, start = self._steps
            return max(math.ceil(progress * count - EPSILON) - (1 if start else 0), 0) / count
        if self._spline is not None and self._spline_fits:
            x1, y1, x2, y2 = self._spline
            return spline_at(self._spline, spline_param((y1, x1, y2, x2), progress))[0]
        grid = [i / EASE_GRID for i in range(EASE_GRID + 1)]
        upper = next((t for t in grid if self(t) >= progress - EPSILON), None)
        if upper is None:
            return 1.0
        low, high = max(upper - 1 / EASE_GRID, 0.0), upper
        for _ in range(EASE_BISECTIONS):
            middle = (low + high) / 2
            low, high = (middle, high) if self(middle) < progress else (low, middle)
        return high

    @property
    def _spline_fits(self) -> bool:
        return self._spline is not None and all(0.0 <= v <= 1.0 for v in self._spline)

    def _sample_count(self) -> int:
        """Samples for a function: more the more the curve bends (total slope change on a fine grid)."""
        step = 1 / EASE_GRID
        points = [self(i * step) for i in range(EASE_GRID + 1)]
        bend = sum(abs(points[i + 1] - 2 * points[i] + points[i - 1]) for i in range(1, EASE_GRID)) / step
        low, high = EASE_SAMPLES
        return int(min(max(low + bend * EASE_BEND_SAMPLES, low), high))

    def smil(self, values: Sequence[str], key_times: Sequence[float] | None = None, *,
             discrete: bool = False) -> dict[str, Any]:
        """SMIL timing attributes that play *values* along this curve over the whole timeline.

        Parameters
        ----------
        values : sequence of str
            The animation's values.
        key_times : sequence of float, optional
            Their times, evenly spread when omitted.
        discrete : bool, optional
            Whether the animation jumps between values (``calcMode="discrete"``).
            Defaults to False.

        Returns
        -------
        dict
            Some of ``values``, ``key_times``, ``key_splines`` and
            ``calc_mode``, in Python spelling; empty for a linear curve.

        Examples
        --------
        >>> Ease("ease-in").smil(["0", "10", "20"])["key_times"]
        [0.0, 0.6575, 1.0]
        """
        if self.linear or not values:
            return {}
        keys = _keys(len(values), key_times, discrete)
        if discrete:
            return {"key_times": [_number(self.time_of(k)) for k in keys]}
        if self._spline_fits:
            assert self._spline is not None
            x1, y1, x2, y2 = self._spline
            params = [spline_param((y1, x1, y2, x2), k) for k in keys]
            times = [_number(spline_at(self._spline, s)[0]) for s in params]
            times[0], times[-1] = 0.0, 1.0
            splines = [split_spline(self._spline, a, b) for a, b in zip(params, params[1:], strict=False)]
            return {"calc_mode": "spline", "key_times": times, "key_splines": splines or None}
        if self._steps is not None:
            count, start = self._steps
            moments = [i / count for i in range(count + (0 if start else 1))]
            return {"calc_mode": "discrete", "key_times": [_number(t) for t in moments],
                    "values": [_value_at(values, keys, self(t)) for t in moments]}
        count = self._sample_count()
        moments = [i / count for i in range(count + 1)]
        return {"calc_mode": "linear", "key_times": [_number(t) for t in moments],
                "values": [_value_at(values, keys, self(t)) for t in moments]}


EaseLike: TypeAlias = Ease | str | tuple[float, float, float, float] | tuple[Any, ...] | Callable[[float], float]
"""Anything ``ease=`` takes: an :class:`Ease`, a curve name, a bézier 4-tuple, ``("steps", n)`` or a function."""


def _split(value: Any) -> list[str] | None:
    return None if value is None else [v.strip() for v in str(value).split(";") if v.strip()]


def apply_ease(element: Element, ease: EaseLike, values_attribute: str = "values") -> None:
    """Rewrite *element*'s timing attributes so it plays along *ease*.

    *values_attribute* names the list the curve runs through (``keyPoints``
    for motion along a path). Raises ValueError when ``calcMode`` is paced or
    spline already, or when a sampled curve has no start value to work from.
    """
    curve = Ease(ease)
    mode = str(getattr(element.get("calcMode"), "value", element.get("calcMode")))
    if mode in ("paced", "spline"):
        raise ValueError(f"ease= replaces calcMode; drop calc_mode={mode!r}")
    if curve.linear:
        return
    values = _split(element.get(values_attribute))
    start, stop, by = element.get("from"), element.get("to"), element.get("by")
    if values is None and values_attribute == "values" and (stop is not None or by is not None):
        if start is not None:
            values = [str(start), str(stop) if stop is not None else add_values(str(start), str(by))]
        elif curve._spline_fits or mode == "discrete":
            values = ["", ""]
        else:
            raise ValueError("a sampled ease needs from_= (or values=) to know where it starts")
    if values is None:
        values = ["0", "1"]
    keys = element.get("keyTimes")
    timing = curve.smil(values, [float(k) for k in _split(keys) or []] or None, discrete=mode == "discrete")
    if "values" in timing:
        for name in ("from", "to", "by"):
            element.discard(name)
        element.set(values_attribute, ";".join(timing.pop("values")))
    elif values_attribute != "values" and element.get(values_attribute) is None:
        element.set(values_attribute, "0;1")
    if timing.get("key_splines"):
        timing["key_splines"] = ";".join(" ".join(f"{n:g}" for n in s) for s in timing["key_splines"])
    timing["key_times"] = ";".join(f"{t:g}" for t in timing["key_times"])
    element.update(**timing)
