from collections.abc import Iterable
from typing import Any
from ..elements.core import Element
from ..pathdata.data import PathData
from ._typing import Stack

__all__ = [
    "attach_cursor",
    "clip_outline",
    "cursor_of",
    "element_list",
    "replace_in_parent",
    "resolve",
]

def resolve(element: Element, value: Any) -> Element | None: ...

def clip_outline(element: Element) -> PathData | None: ...

def replace_in_parent(old: Element, new: Element) -> None: ...

def attach_cursor(element: Element, stack: Stack[Element] | None) -> None: ...

def cursor_of(element: Element) -> Stack[Element] | None: ...

def element_list(items: Element | str | Iterable[Element]) -> list[Element | str]: ...
