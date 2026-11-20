from collections.abc import Callable
from typing import Any, Generic, TypeVar, overload
from ..elements.base import Element
from .length import Length

__all__ = ["Attr", "LengthAttr"]

T = TypeVar('T')

class Attr(Generic[T]):
    svg: Any
    name: str
    convert: Callable[[Any], T] | None
    default: T | None

    def __init__(
        self,
        name: str | None = None,
        *,
        convert: Callable[[Any], T] | None = None,
        default: T | None = None,
    ) -> None: ...
    def __set_name__(self, owner: type, name: str) -> None: ...
    @overload
    def __get__(self, obj: None, owner: type | None = None) -> Attr[T]: ...
    @overload
    def __get__(self, obj: Element, owner: type | None = None) -> T | None: ...
    def __set__(self, obj: Element, value: T | str | None) -> None: ...
    def __delete__(self, obj: Element) -> None: ...
    @property
    def key(self) -> str: ...
    def __repr__(self) -> str: ...

class LengthAttr(Attr[float | Length]):
    def __get__(self, obj: Element | None, owner: type | None = None) -> Any: ...
