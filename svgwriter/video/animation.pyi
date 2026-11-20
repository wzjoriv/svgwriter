from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Final, TypeAlias
from .._internal._registry import Registry
from .._internal._typing import AnyPath
from ..document import Document
from .frames import Frame, FrameData

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

Renderer: TypeAlias = Callable[[Document, float], FrameData]
Update: TypeAlias = Callable[[Document, float], object]
DEFAULT_FPS: Final = ...
RENDERERS: Final[Registry[Callable[[Document, float], FrameData]]]

def register_renderer(name: str) -> Callable[[Renderer], Renderer]: ...

def unregister_renderer(name: str) -> None: ...

def resolve_renderer(renderer: Renderer | str | None) -> Renderer: ...

def animation_duration(document: Document) -> float | None: ...

def iter_frames(
    document: Document,
    fps: float = 30.0,
    duration: float | None = None,
    renderer: Renderer | str | None = None,
    *,
    update: Update | None = None,
) -> Iterator[Frame]: ...

def render_animation(
    document: Document,
    path: AnyPath,
    fps: float = 30.0,
    duration: float | None = None,
    renderer: Renderer | str | None = None,
    *,
    update: Update | None = None,
    ffmpeg: str | None = None,
) -> Path: ...
