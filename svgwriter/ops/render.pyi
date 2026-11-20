import numpy as np
import skia
from collections.abc import Callable
from typing import Any, Final
from numpy import ndarray
from ..attributes.viewbox import ViewBox
from ..color.color import ColorLike
from ..document import Document
from ..elements.base import Element
from ..transform.matrix import Matrix

__all__ = [
    "DEFAULT_SIZE",
    "document_size",
    "encode",
    "encode_image",
    "paint_tree",
    "rasterize",
    "render_png",
    "render_svg",
    "render_tree",
    "render_frame",
]

DEFAULT_SIZE: Final = ...

def document_size(document: Document) -> tuple[float, float]: ...

def render_svg(
    text: str,
    width: float,
    height: float,
    *,
    scale: float = 1.0,
    background: ColorLike | None = None,
) -> np.ndarray: ...

def render_tree(
    root: Element,
    wrap: Callable[[str], str],
    width: float,
    height: float,
    *,
    view: Matrix = ...,
    scale: float = 1.0,
    background: ColorLike | None = None,
    viewport: bool = False,
    view_box: ViewBox | None = None,
    snapshot: bool = False,
) -> Any: ...

def paint_tree(
    canvas: skia.Canvas,
    root: Element,
    wrap: Callable[[str], str],
    width: float,
    height: float,
    *,
    view: Matrix = ...,
    viewport: bool = False,
    view_box: ViewBox | None = None,
    native_text: bool = False,
) -> None: ...

def rasterize(
    document: Document,
    *,
    scale: float = 1.0,
    size: tuple[int, int] | int | None = None,
    padding: float = 0.0,
    background: ColorLike | None = None,
    snapshot: bool = False,
) -> Any: ...

def encode_image(
    image: Any,
    format: str = 'png',
    *,
    quality: int = 90,
) -> bytes: ...

def encode(
    pixels: ndarray,
    format: str = 'png',
    *,
    quality: int = 90,
) -> bytes: ...

def render_png(
    document: Document,
    *,
    scale: float = 1.0,
    background: ColorLike | None = None,
) -> bytes: ...

def render_frame(document: Document, time: float) -> np.ndarray: ...
