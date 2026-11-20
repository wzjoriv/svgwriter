from collections.abc import Callable
from ..attributes.viewbox import ViewBox
from ..document import Document
from ..elements import Text
from ..elements.core import Element
from ..pathdata.data import BBox
from ..transform.matrix import Matrix

__all__ = [
    "ellipses_as_paths",
    "expand_image_patterns",
    "outlined",
    "page_box",
    "renderable_copy",
    "view_matrix",
]

def expand_image_patterns(root: Element) -> None: ...

def ellipses_as_paths(root: Element) -> None: ...

def outlined(text: Text) -> Element: ...

def renderable_copy(
    root: Element,
    *,
    keep_text: Callable[[Text], bool] | None = None,
) -> Element: ...

def view_matrix(
    document: Document,
    width: float,
    height: float,
    box: ViewBox | None = None,
) -> Matrix: ...

def page_box(document: Document, element: Element) -> tuple[BBox | None, float]: ...
