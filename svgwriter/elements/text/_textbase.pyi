from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias
from ..._internal._typing import LengthAdjust
from ...attributes.length import LengthLike
from ..core import Child, Element
from ..core._element import AttrValue

__all__ = ["Coordinates"]

Coordinates: TypeAlias = LengthLike | Sequence[LengthLike]

class _TextPositioning(Element):
    def __init__(
        self,
        *args: Child,
        x: Coordinates | None = None,
        y: Coordinates | None = None,
        dx: Coordinates | None = None,
        dy: Coordinates | None = None,
        rotate: float | Sequence[float] | None = None,
        decoration=None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
    @property
    def text_content(self) -> str: ...
    @text_content.setter
    def text_content(self, value: str) -> None: ...

class _TextLength(Element):
    def __init__(
        self,
        *args: Child,
        text_length: LengthLike | None = None,
        length_adjust: LengthAdjust | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> None: ...
