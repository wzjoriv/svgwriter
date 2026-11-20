from collections.abc import Mapping
from typing import Any
from ._categories import ContentModel
from .base import AttrValue, Child, Element

__all__ = ["UnknownElement"]

class UnknownElement(Element, content=ContentModel.MIXED):
    namespace: str | None
    tag: str

    def __init__(
        self,
        tag: str,
        *children: Child,
        namespace: str | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
