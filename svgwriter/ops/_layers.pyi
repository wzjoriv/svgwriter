import skia
from ..elements.core._element import Element
from ..elements.structure import Image
from ..transform.matrix import Matrix

__all__ = ["draw_image", "drawable_order", "hidden", "image_matrix", "layers"]

def drawable_order(root: Element) -> list[Element]: ...

def layers(root: Element) -> list[tuple[list[Element], Element | None]]: ...

def image_matrix(image: Image) -> Matrix: ...

def hidden(root: Element, keep: list[Element]) -> list[Element]: ...

def draw_image(
    canvas: skia.Canvas,
    image: Image,
    root: Element,
    view: Matrix,
) -> None: ...
