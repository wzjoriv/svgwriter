from typing import Any
from ..document import Document
from ..elements.base import Element

__all__ = ["to_matplotlib"]

def to_matplotlib(
    item: Element | Document,
    ax: Any,
    *,
    flip: bool = True,
) -> list[Any]: ...
