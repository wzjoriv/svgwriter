from collections.abc import Callable
from ..elements.base import Element
from ..elements.text import Text

__all__ = ["ellipses_as_paths", "expand_image_patterns", "outlined", "renderable_copy"]

def expand_image_patterns(root: Element) -> None: ...

def ellipses_as_paths(root: Element) -> None: ...

def outlined(text: Text) -> Element: ...

def renderable_copy(
    root: Element,
    *,
    keep_text: Callable[[Text], bool] | None = None,
) -> Element: ...
