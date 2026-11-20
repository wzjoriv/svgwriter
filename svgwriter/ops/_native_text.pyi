import skia
from ..elements.core import Element
from ..elements.text import Text
from ..transform.matrix import Matrix

__all__ = ["draw_text", "native_text"]

def native_text(text: Text) -> bool: ...

def draw_text(
    canvas: skia.Canvas,
    text: Text,
    root: Element,
    view: Matrix,
    *,
    only_color: bool = False,
    searchable: bool = False,
) -> None: ...
