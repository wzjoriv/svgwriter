from collections.abc import Mapping
from typing import Any
from ._categories import Category
from ._element import E, Element

__all__ = ["Construction"]

class Construction:
    @classmethod
    def lookup(cls, tag: str) -> type[Element] | None: ...
    @classmethod
    def registered(cls, category: Category | None = None) -> dict[str, type[Element]]: ...
    @classmethod
    def from_attributes(cls: type[E], attributes: Mapping[str, str]) -> E: ...
    @classmethod
    def many(cls: type[E], **columns: Any) -> list[E]: ...
