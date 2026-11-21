"""Turning documents into video and GIF files through ffmpeg.

svgwriter does not rasterize by itself. A *renderer* is any callable
``renderer(document, seconds)`` returning PNG bytes or an
``(height, width, 4)`` uint8 RGBA array; frames are piped to ``ffmpeg``.
The ``"skia"`` renderer is built in. A :class:`Scene` subclass bundles a
drawing, its ``update`` and its settings, so one file can hold several
animations.

Example
-------
>>> import svgwriter as svg
>>> doc = svg.Document(64, 64)
>>> dot = doc.circle(32, 32, 4, fill="tomato")
>>> def grow(document, t):
...     dot.r = 4 + 20 * t
>>> doc.render_animation("grow.gif", fps=12, duration=1, renderer="skia", update=grow)  # doctest: +SKIP
"""

from __future__ import annotations

from . import behaviors
from ._ffmpeg import find_ffmpeg
from .animation import (
    DEFAULT_FPS,
    Renderer,
    Update,
    animation_duration,
    iter_frames,
    render_animation,
    renderers,
    resolve_renderer,
)
from .frames import Frame, FrameData, RGBAArray, frame_times
from .loader import load_scenes
from .reader import Video
from .scene import Scene

__all__ = [
    "Scene",
    "behaviors",
    "Video",
    "DEFAULT_FPS",
    "renderers",
    "Frame",
    "FrameData",
    "RGBAArray",
    "Renderer",
    "Update",
    "animation_duration",
    "find_ffmpeg",
    "frame_times",
    "iter_frames",
    "load_scenes",
    "render_animation",
    "resolve_renderer",
]
