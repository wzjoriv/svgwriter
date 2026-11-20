import skia
from ..elements import Image
from ..elements.core import Element
from ..transform.matrix import Matrix

__all__ = ["draw_image", "hidden", "layers"]

def layers(root: Element) -> list[tuple[list[Element], Element | None]]: ...

def hidden(root: Element, keep: list[Element]) -> list[Element]: ...

def draw_image(
    canvas: skia.Canvas,
    image: Image,
    root: Element,
    view: Matrix,
) -> None: ...
