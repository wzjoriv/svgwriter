import numpy as np
from typing import Any, Final
from numpy import ndarray
from ..color.color import ColorLike
from ..document import Document
from ._painting import paint_tree as paint_tree, render_tree as render_tree

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
