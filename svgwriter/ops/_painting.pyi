import skia
from collections.abc import Callable
from typing import Any
from ..attributes.viewbox import ViewBox
from ..color.color import ColorLike
from ..elements.core import Element
from ..transform.matrix import Matrix

__all__ = ["paint_tree", "render_tree"]

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
