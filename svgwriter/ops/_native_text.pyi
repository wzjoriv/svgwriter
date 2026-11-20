import skia
from ..elements.base import Element
from ..elements.text import Text
from ..transform.matrix import Matrix

__all__ = ["draw_text", "native_text"]

def native_text(text: Text) -> bool: ...

def draw_text(
    canvas: skia.Canvas,
    text: Text,
    root: Element,
    view: Matrix,
) -> None: ...
