from collections.abc import Iterable
from .base import Element
from .structure import Group

__all__ = ["Composable"]

class Composable:
    def __add__(self: Element, other: Element | Iterable[Element]) -> Group: ...
    def __iadd__(self: Element, other: Element | Iterable[Element]) -> Group: ...
    def __radd__(self: Element, other: Iterable[Element]) -> Group: ...
