from ..attributes.viewbox import PreserveAspectRatio
from ..elements.core import Element
from ..elements.structure import Image
from ..transform.matrix import Matrix

__all__ = ["ancestry", "drawable_order", "fit_box", "image_matrix", "resolve_links"]

def drawable_order(root: Element) -> list[Element]: ...

def resolve_links(root: Element) -> None: ...

def fit_box(
    box_w: float,
    box_h: float,
    w: float,
    h: float,
    ratio: PreserveAspectRatio,
) -> Matrix: ...

def image_matrix(image: Image) -> Matrix: ...

def ancestry(element: Element, root: Element) -> tuple[Matrix, float]: ...
