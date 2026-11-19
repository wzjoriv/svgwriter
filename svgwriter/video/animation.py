"""Rendering a document over time and encoding the frames."""

from __future__ import annotations

import importlib
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypeAlias

from .._internal._registry import Registry
from .._internal._typing import AnyPath
from ._ffmpeg import encode, find_ffmpeg
from .frames import Frame, FrameData, frame_times, to_frame

if TYPE_CHECKING:
    from ..document import Document

__all__ = [
    "DEFAULT_FPS",
    "RENDERERS",
    "Renderer",
    "Update",
    "animation_duration",
    "iter_frames",
    "register_renderer",
    "render_animation",
    "resolve_renderer",
    "unregister_renderer",
]

Renderer: TypeAlias = "Callable[[Document, float], FrameData]"
"""``renderer(document, seconds)`` returning PNG bytes or an RGBA array."""

Update: TypeAlias = "Callable[[Document, float], object]"
"""``update(document, seconds)`` changing the document before each frame."""

DEFAULT_FPS: Final = 30.0
_CLOCK_RE: Final = re.compile(r"^\s*([+-]?\d*\.?\d+)\s*(ms|s|min|h)?\s*$")
_CLOCK_SCALE: Final = {"ms": 0.001, "s": 1.0, "min": 60.0, "h": 3600.0, None: 1.0}

RENDERERS: Final[Registry[Callable[[Document, float], FrameData]]] = Registry("renderer")


def _skia(document: Document, time: float) -> FrameData:
    from ..ops.render import skia_renderer

    return skia_renderer(document, time)


RENDERERS.add("skia", _skia)


def register_renderer(name: str) -> Callable[[Renderer], Renderer]:
    """Decorator registering a renderer so it can be chosen by *name*.

    A rasterizer package can register itself on import, after which
    ``renderer="myraster"`` selects it everywhere a renderer is accepted.

    Parameters
    ----------
    name : str
        The name to register the renderer under.

    Returns
    -------
    callable
        A decorator that registers the function and returns it unchanged.

    See Also
    --------
    resolve_renderer : Look a registered renderer up again.

    Examples
    --------
    >>> from svgwriter.video import register_renderer, resolve_renderer, unregister_renderer
    >>> @register_renderer("myraster")
    ... def render(document, seconds):
    ...     return document.render_png()
    >>> resolve_renderer("myraster") is render
    True
    >>> unregister_renderer("myraster")
    """
    return RENDERERS.register(name)  # type: ignore[return-value]


def unregister_renderer(name: str) -> None:
    """Remove the renderer registered under *name*.

    Parameters
    ----------
    name : str
        The name given to :func:`register_renderer`.

    Raises
    ------
    KeyError
        When no renderer has that name.

    Examples
    --------
    >>> from svgwriter.video import register_renderer, unregister_renderer
    >>> _ = register_renderer("tmp")(lambda document, seconds: b"")
    >>> unregister_renderer("tmp")
    """
    RENDERERS.remove(name)


def resolve_renderer(renderer: Renderer | str | None) -> Renderer:
    """Return a renderer from a callable, a registered name or ``"module:function"``.

    Parameters
    ----------
    renderer : callable, str or None
        A renderer, the name of a registered one, or a ``"module:function"``
        import path.

    Returns
    -------
    callable
        ``renderer(document, seconds)`` returning PNG bytes or an RGBA array.

    Raises
    ------
    ValueError
        If `renderer` is None or an unregistered name without a colon.
    TypeError
        If a ``"module:function"`` path names something that is not callable.

    See Also
    --------
    register_renderer : Add a named renderer.

    Examples
    --------
    >>> from svgwriter.video import resolve_renderer
    >>> callable(resolve_renderer("skia"))
    True
    >>> resolve_renderer("nope")
    Traceback (most recent call last):
    ...
    ValueError: unknown renderer 'nope'; registered: skia
    """
    if callable(renderer):
        return renderer
    if renderer is None:
        names = ", ".join(RENDERERS.names())
        raise ValueError(
            "no renderer given; pass renderer=callable(document, seconds) returning PNG bytes or an RGBA array, "
            f"a registered name ({names}) or 'module:function'"
        )
    if renderer in RENDERERS:
        return RENDERERS.get(renderer)
    module_name, sep, attribute = renderer.partition(":")
    if not sep:
        raise ValueError(f"unknown renderer {renderer!r}; registered: {', '.join(RENDERERS.names())}")
    found = getattr(importlib.import_module(module_name), attribute)
    if not callable(found):
        raise TypeError(f"{renderer!r} is not callable")
    return found  # type: ignore[no-any-return]


def _seconds(value: object) -> float | None:
    match = _CLOCK_RE.match(str(value))
    if match is None:
        return None
    return float(match.group(1)) * _CLOCK_SCALE[match.group(2)]


def animation_duration(document: Document) -> float | None:
    """End of the last SMIL animation (``begin + dur``) in seconds.

    Only plain clock values count; event or syncbase timings are ignored.

    Parameters
    ----------
    document : Document
        The drawing to inspect.

    Returns
    -------
    float or None
        The end time in seconds, or None when no animation qualifies.

    See Also
    --------
    iter_frames : Uses this as the default duration.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.video import animation_duration
    >>> doc = svg.Document(10, 10)
    >>> animation_duration(doc) is None
    True
    """
    from ..elements.animation import AnimationElement

    ends = []
    for element in document.root.find_all(AnimationElement):
        dur = _seconds(element.get("dur", ""))
        if dur is not None:
            ends.append((_seconds(element.get("begin", 0)) or 0.0) + dur)
    return max(ends) if ends else None


def iter_frames(
    document: Document,
    fps: float = DEFAULT_FPS,
    duration: float | None = None,
    renderer: Renderer | str | None = None,
    *,
    update: Update | None = None,
) -> Iterator[Frame]:
    """Render one frame per ``1/fps`` seconds without encoding them.

    Frames are produced lazily, so the document can be changed by `update`
    between them.

    Parameters
    ----------
    document : Document
        The drawing.
    fps : float, optional
        Frames per second. Defaults to 30.0.
    duration : float, optional
        Seconds to render. Defaults to the end of the document's SMIL animations.
    renderer : callable, str or None, optional
        ``renderer(document, seconds)``, a registered name such as ``"skia"`` or
        ``"module:function"``. Defaults to None, which raises; there is no
        default renderer.
    update : callable, optional
        ``update(document, seconds)`` called before each frame. Defaults to None.

    Yields
    ------
    Frame
        The checked frame for each sample time.

    Raises
    ------
    ValueError
        If no renderer is given, or no duration is given and the document has no
        plain-clock SMIL animation.

    See Also
    --------
    render_animation : Encode the frames into a file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.video import iter_frames
    >>> doc = svg.Document(8, 6)
    >>> [(f.index, f.width, f.height) for f in iter_frames(doc, fps=2, duration=1, renderer="skia")]
    [(0, 8, 6), (1, 8, 6)]
    """
    draw = resolve_renderer(renderer)
    length = duration if duration is not None else animation_duration(document)
    if length is None:
        raise ValueError("pass duration=...; the document has no SMIL animation with a plain 'dur'")
    for index, time in enumerate(frame_times(fps, length)):
        if update is not None:
            update(document, time)
        yield to_frame(index, time, draw(document, time))


def render_animation(
    document: Document,
    path: AnyPath,
    fps: float = DEFAULT_FPS,
    duration: float | None = None,
    renderer: Renderer | str | None = None,
    *,
    update: Update | None = None,
    ffmpeg: str | None = None,
) -> Path:
    """Render frames and encode them with ffmpeg.

    ffmpeg is located first, so a missing executable fails before any frame is
    rendered. Frames are piped to a single ffmpeg process.

    Parameters
    ----------
    document : Document
        The drawing.
    path : str or path-like
        Output file; the extension picks the encoder (``.mp4``, ``.gif``,
        ``.webm``, ``.mov``, ``.apng``, anything else ffmpeg knows).
    fps : float, optional
        Frames per second. Defaults to 30.0.
    duration : float, optional
        Seconds to render. Defaults to the end of the document's SMIL
        animations.
    renderer : callable, str, optional
        ``renderer(document, seconds)`` returning PNG bytes or an
        ``(height, width, 4)`` uint8 array; a registered name such as
        ``"skia"``; or ``"module:function"``. Defaults to None, which raises;
        there is no default renderer.
    update : callable, optional
        ``update(document, seconds)`` called before each frame, for
        procedural animation. Defaults to None.
    ffmpeg : str, optional
        The ffmpeg executable. Defaults to ``ffmpeg`` found on ``PATH``.

    Returns
    -------
    pathlib.Path
        The written file.

    Raises
    ------
    FFmpegNotFoundError
        Before rendering anything, when ffmpeg is missing.
    FFmpegError
        When ffmpeg fails.
    ValueError
        If no renderer or duration can be determined.

    See Also
    --------
    iter_frames : The frames without encoding.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.video import FFmpegNotFoundError, render_animation
    >>> doc = svg.Document(8, 6)
    >>> try:
    ...     render_animation(doc, "out.gif", duration=1, renderer="skia", ffmpeg="no-such-ffmpeg")
    ... except FFmpegNotFoundError:
    ...     print("ffmpeg is required")
    ffmpeg is required
    """
    executable = find_ffmpeg(ffmpeg)
    frames = iter_frames(document, fps, duration, renderer, update=update)
    encode(frames, path, fps, executable=executable)
    return Path(path)
