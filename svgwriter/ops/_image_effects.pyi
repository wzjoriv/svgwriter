import skia
from collections.abc import Callable
from typing import Any
from ..elements.base import Element

__all__ = ["image_filter", "paint_mask"]

def image_filter(filter_element: Element) -> Any: ...

def paint_mask(
    canvas: skia.Canvas,
    mask: Element,
    paint_svg: Callable[[skia.Canvas, str, float, float], None],
) -> None: ...
