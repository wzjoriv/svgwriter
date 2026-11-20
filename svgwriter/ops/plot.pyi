from typing import Any
from ..document import Document
from ..elements.core._element import Element

__all__ = ["to_matplotlib"]

def to_matplotlib(
    item: Element | Document,
    ax: Any,
    *,
    flip: bool = True,
) -> list[Any]: ...
