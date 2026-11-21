"""
``svg.sweep``: a drawing function's parameters stepped over time, as a scene that saves to SVG, GIF, MP4 and PowerPoint.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from numbers import Real
from pathlib import Path
from typing import Any

from ..._internal._codecs._gif import encode_gif_animation
from ..._internal._codecs._rgba import to_uint8
from ..._internal._typing import AnyPath
from ...model.attributes import Length, ViewBox
from ...model.color import parse_color
from ...model.elements.animation import Ease, EaseLike
from ...model.pathdata import BBox
from ...motion.video import DEFAULT_FPS, Renderer, Scene, frame_times
from ...ops import interpolate
from ._choices import ColorPicker, Dropdown, MultiSelect, Text, Toggle, hex_color
from ._constants import BOUNDS_SAMPLES, GIF_SUFFIX, SWEEP_DURATION
from ._control import Control
from ._draw import draw, morph
from ._infer import accepts, controls_of, is_color
from ._numbers import IntSlider, Number, RangeSlider, Slider

__all__ = ["Sweep", "sweep"]

Track = Callable[[float], Any]


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _steps(values: Sequence[Any]) -> Track:
    items = list(values)
    if not items:
        raise ValueError("a list to step through must not be empty")
    return lambda progress: items[min(int(progress * len(items)), len(items) - 1)]


def _between(start: Any, end: Any, whole: bool = False) -> Track:
    if _is_number(start) and _is_number(end):
        return lambda p: round(start + (end - start) * p) if whole else start + (end - start) * p
    if isinstance(start, Length) and isinstance(end, Length):
        if start.unit != end.unit:
            raise ValueError(f"sweep ends need one unit, got {start} and {end}")
        return lambda p: Length(start.value + (end.value - start.value) * p, start.unit)
    if is_color(start) and is_color(end):
        low, high = parse_color(hex_color(start)), parse_color(hex_color(end))
        return lambda p: hex_color(interpolate(low, high, p))
    raise TypeError(f"cannot sweep from {start!r} to {end!r}; give numbers, lengths or colours, or a list")


def _track(spec: Any, declared: Control | None) -> Track | None:
    """How a sweep argument changes with progress ``0..1``; None for a fixed value."""
    if isinstance(spec, Slider):
        return lambda p: spec.argument(_between(spec.min, spec.max, isinstance(spec, IntSlider))(p))
    if isinstance(spec, Dropdown) and not isinstance(spec, MultiSelect):
        return _steps(spec.values)
    if isinstance(spec, Toggle):
        return _steps((False, True))
    if isinstance(spec, (RangeSlider, MultiSelect, ColorPicker, Text, Number, Control)):
        return None
    if isinstance(spec, tuple) and len(spec) == 2:
        return _between(*spec, whole=isinstance(declared, IntSlider))
    if isinstance(spec, list):
        return _steps(spec)
    return None


class Sweep(Scene):
    """A drawing function called with parameters that change over time; :func:`sweep` makes one.

    A :class:`~svgwriter.Scene`: :meth:`save` writes GIF and MP4 through ffmpeg and bakes SVG, HTML and
    PowerPoint into SMIL. Each frame redraws the function and carries the result over onto the scene's
    drawing, so elements that keep their place change attributes smoothly in the baked SVG.

    Parameters
    ----------
    function : callable
        Returns a :class:`~svgwriter.Document` or an element.
    tracks : mapping of str to callable
        For each swept parameter, its value at progress ``0..1``.
    fixed : mapping of str to object
        Arguments that do not change.
    duration : float
        Seconds from the first value to the last.
    fps : float, optional
        Frames per second. Defaults to the scene default, 30.
    ease : str, tuple or callable, optional
        A timing curve as :class:`~svgwriter.Ease` takes. Defaults to None (linear).
    name : str, optional
        Output name. Defaults to the function's name.

    See Also
    --------
    sweep : Build one from ranges and lists.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.tools.widgets import Sweep
    >>> grow = Sweep(lambda r: svg.circle(20, 20, r), {"r": lambda p: 2 + 18 * p}, {}, duration=1.0, fps=4)
    >>> grow.values_at(0.5)
    {'r': 11.0}
    """

    def __init__(self, function: Callable[..., Any], tracks: Mapping[str, Track], fixed: Mapping[str, Any], *,
                 duration: float, fps: float | None = None, ease: EaseLike | None = None,
                 name: str | None = None) -> None:
        if duration <= 0:
            raise ValueError(f"duration must be positive, got {duration:g}")
        self.function, self.tracks, self.fixed = function, dict(tracks), dict(fixed)
        self.ease = Ease(ease) if ease is not None else None
        self.fps, self.duration = fps or DEFAULT_FPS, duration  # type: ignore[misc]
        self._last: list[Any] | None = None
        first = draw(function, self.values_at(0.0))
        self._sized = first.root.get("viewBox") is not None
        if not self._sized:
            self._frame(first, self._bounds(first))
        super().__init__(first, name=name or getattr(function, "__name__", "sweep"))
        box = first.root.get("viewBox")
        self.width, self.height = (box.width, box.height) if box is not None else (self.width, self.height)  # type: ignore[misc]

    def values_at(self, seconds: float) -> dict[str, Any]:
        """The arguments at *seconds*.

        Parameters
        ----------
        seconds : float
            Time since the start; clamped to the duration.

        Returns
        -------
        dict
            One value per parameter, swept and fixed.

        Examples
        --------
        >>> import svgwriter as svg
        >>> fade = svg.sweep(lambda tone: svg.rect(0, 0, 10, 10, fill=tone), tone=("#000000", "#ffffff"))
        >>> fade.values_at(1.0)
        {'tone': '#808080'}
        """
        progress = min(max(seconds / self.duration, 0.0), 1.0)  # type: ignore[operator]
        if self.ease is not None:
            progress = self.ease(progress)
        return {**self.fixed, **{name: track(progress) for name, track in self.tracks.items()}}

    def _bounds(self, first: Any) -> BBox | None:
        boxes = [first.content_bounds()]
        for index in range(1, BOUNDS_SAMPLES):
            seconds = self.duration * index / (BOUNDS_SAMPLES - 1)  # type: ignore[operator]
            boxes.append(draw(self.function, self.values_at(seconds)).content_bounds())
        found = [box for box in boxes if box is not None]
        if not found:
            return None
        left, top = min(box.x for box in found), min(box.y for box in found)
        right, bottom = max(box.x + box.width for box in found), max(box.y + box.height for box in found)
        return BBox(left, top, right - left, bottom - top)

    @staticmethod
    def _frame(document: Any, box: BBox | None) -> None:
        if box is not None:
            for name, value in (("width", box.width), ("height", box.height),
                                ("viewBox", ViewBox(box.x, box.y, box.width, box.height))):
                document.root.set(name, value)

    def update(self, seconds: float) -> None:
        """Redraw the function for the values at *seconds* onto the scene's drawing.

        Parameters
        ----------
        seconds : float
            Time since the start.

        Examples
        --------
        >>> import svgwriter as svg
        >>> grow = svg.sweep(lambda r: svg.circle(20, 20, r), r=(2, 20), dur=1)
        >>> grow.update(1.0)
        >>> grow.document.root[0].get("r")
        20.0
        """
        values = self.values_at(seconds)
        key = [(name, repr(value)) for name, value in values.items()]
        if key == self._last:
            return
        self._last = key
        morph(self.document.root, draw(self.function, values).root, attributes=self._sized)

    def save(self, path: AnyPath | None = None, *, fps: float | None = None, duration: float | None = None,
             renderer: Renderer | str | None = None, ffmpeg: str | None = None) -> Path:
        """Save the sweep; ``.gif`` is encoded here, frame by frame, without ffmpeg.

        Parameters
        ----------
        path : str or path-like, optional
            Output file; the extension picks the format as for :meth:`Scene.save <svgwriter.Scene.save>`.
            Defaults to ``<name>.mp4``.
        fps : float, optional
            Overrides the sweep's ``fps``.
        duration : float, optional
            Overrides the sweep's duration.
        renderer : callable or str, optional
            The renderer for video formats.
        ffmpeg : str, optional
            The ffmpeg executable for video formats.

        Returns
        -------
        pathlib.Path
            The written file.

        Examples
        --------
        >>> import svgwriter as svg
        >>> grow = svg.sweep(lambda r: svg.circle(20, 20, r), r=(2, 20), dur=1, fps=4)
        >>> grow.save("grow.gif")  # doctest: +SKIP
        """
        target = Path(path) if path is not None else None
        if target is None or target.suffix.lower() != GIF_SUFFIX:
            return super().save(path, fps=fps, duration=duration, renderer=renderer, ffmpeg=ffmpeg)
        rate, length = fps or self.fps, duration or self.duration
        frames = []
        for seconds in frame_times(rate, length):  # type: ignore[arg-type]
            self._advance(self.document, seconds)
            frames.append(to_uint8(self.document.at(seconds).rasterize()))
        target.write_bytes(encode_gif_animation(frames, rate))
        return target


def sweep(function: Callable[..., Any], *, dur: float = SWEEP_DURATION, fps: float | None = None,
          ease: EaseLike | None = None, name: str | None = None, **params: Any) -> Sweep:
    """Step *function*'s parameters over time and return the animation as a scene.

    Each keyword is a parameter: ``(start, end)`` of numbers, lengths or colours runs smoothly from one to
    the other (whole numbers when the parameter is declared with an :class:`IntSlider`); a list steps
    through its items; a slider runs from its ``min`` to its ``max``, options and
    toggles step through their values. Anything else is passed unchanged, and parameters with declared
    controls (:func:`~svgwriter.tools.widgets.controls`) that are not given keep their starting value.

    Parameters
    ----------
    function : callable
        Returns a :class:`~svgwriter.Document` or an element.
    dur : float, optional
        Seconds from start to end. Defaults to 2.
    fps : float, optional
        Frames per second. Defaults to 30.
    ease : str, tuple or callable, optional
        Timing curve (``"ease-in-out"``, ...). Defaults to None (linear).
    name : str, optional
        Output name. Defaults to the function's name.
    **params : object
        Ranges, lists, controls and fixed values, by parameter name.

    Returns
    -------
    Sweep
        A scene: ``.save("x.svg")`` bakes SMIL; ``.gif``, ``.mp4`` and ``.pptx`` work as for any scene.

    Raises
    ------
    TypeError
        If a range mixes kinds or a name is not a parameter.

    See Also
    --------
    interact : The same parameters on live controls.

    Examples
    --------
    >>> import svgwriter as svg
    >>> def bar(width=10, color="#0ea5e9"):
    ...     return svg.rect(0, 0, width, 10, fill=color)
    >>> growing = svg.sweep(bar, width=(10, 90), dur=1, fps=4)
    >>> [growing.values_at(t)["width"] for t in (0, 0.5, 1)]
    [10.0, 50.0, 90.0]
    >>> growing.save("bar.svg")  # doctest: +SKIP
    """
    declared = controls_of(function, infer=False)
    tracks, fixed = {}, {}
    for key, control in declared.items():
        if key not in params:
            fixed[key] = control.argument(control.initial)
    accepts(function, list(params))
    for key, value in params.items():
        track = _track(value, declared.get(key))
        if track is not None:
            tracks[key] = track
        else:
            fixed[key] = value.argument(value.initial) if isinstance(value, Control) else value
    return Sweep(function, tracks, fixed, duration=dur, fps=fps, ease=ease, name=name)

