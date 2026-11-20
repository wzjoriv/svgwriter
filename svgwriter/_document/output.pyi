import numpy as np
from os import PathLike
from pathlib import Path as FilePath
from typing import Any, TypeVar
from .._internal._typing import AnyPath
from ..attributes.protocols import TextSink
from ..color.color import ColorLike
from ..document import Document
from ..elements.base import Element
from ..video.animation import Renderer, Update

E = TypeVar('E', bound=Element)

class Output:
    def to_string(self, **options: Any) -> str: ...
    def __str__(self) -> str: ...
    def at(self, time: float) -> Document: ...
    def rasterize(
        self,
        *,
        scale: float = 1.0,
        size: tuple[int, int] | int | None = None,
        padding: float = 0.0,
        background: ColorLike | None = None,
        snapshot: bool = False,
    ) -> np.ndarray: ...
    def render_png(
        self,
        *,
        scale: float = 1.0,
        background: ColorLike | None = None,
    ) -> bytes: ...
    def save(
        self,
        target: AnyPath | TextSink,
        *,
        format: str | None = None,
        time: float | None = None,
        **options: Any,
    ) -> None: ...
    def export(
        self,
        format: str,
        *,
        time: float | None = None,
        **options: Any,
    ) -> bytes | str: ...
    @classmethod
    def open(
        cls,
        path: AnyPath,
        *,
        format: str | None = None,
        **options: Any,
    ) -> Document: ...
    async def save_async(self, path: str | PathLike[str], **options: Any) -> None: ...
    def render_animation(
        self,
        path: AnyPath,
        fps: float = 30.0,
        duration: float | None = None,
        renderer: Renderer | str | None = None,
        *,
        update: Update | None = None,
        ffmpeg: str | None = None,
    ) -> FilePath: ...
