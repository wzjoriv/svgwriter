from collections.abc import Iterable
from ..._internal._constants import DEFAULT_DPI as DEFAULT_DPI
from ...color.color import ColorLike as ColorLike
from ...document import Document as Document
from .._registry import register as register, register_importer as register_importer
from ._constants import DEFAULT_GIF_FPS as DEFAULT_GIF_FPS, DEFAULT_QUALITY as DEFAULT_QUALITY

def gif(
    document: Document,
    *,
    scale: float = 1.0,
    size: tuple[int, int] | int | None = None,
    padding: float = 0.0,
    background: ColorLike | None = None,
    animate: bool | None = None,
    fps: float = 12.0,
    duration: float | None = None,
    loop: int = 0,
    quality: int = 90,
    dpi: float | None = None,
    processes: int | None = 1,
) -> bytes: ...

def ico(
    document: Document,
    *,
    sizes: Iterable[int] = (16, 24, 32, 48, 64, 128, 256),
    padding: float = 0.0,
) -> bytes: ...

def icns(
    document: Document,
    *,
    sizes: Iterable[int] = (16, 32, 64, 128, 256, 512, 1024),
    padding: float = 0.0,
) -> bytes: ...

def read_icon(data: bytes) -> Document: ...

def read_image(data: bytes) -> Document: ...

def read_pnm(data: bytes) -> Document: ...
