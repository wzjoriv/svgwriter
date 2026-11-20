import types
from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager
from typing import Generic, TypeAlias, TypeVar, overload
from ..._internal._typing import Self
from ..structure import Defs
from ._element import Element
from ._factory import ElementFactory

__all__ = ["ChildT", "Container", "GraphicsContainer", "Insertable"]

ChildT = TypeVar('ChildT', bound=Element)
Insertable: TypeAlias = Element | str | Iterable[Element]

class Container(Element, Generic[ChildT]):
    def add(self, child: ChildT) -> ChildT: ...
    def add_all(self, children: Iterable[ChildT]) -> list[ChildT]: ...
    def __iadd__(self, children: ChildT | Iterable[ChildT]) -> Self: ...
    def __iter__(self) -> Iterator[ChildT]: ...
    @overload
    def __getitem__(self, index: int) -> ChildT: ...
    @overload
    def __getitem__(self, index: slice) -> list[ChildT]: ...
    def __setitem__(self, index: int, element: ChildT) -> None: ...

class GraphicsContainer(ElementFactory, AbstractContextManager[GraphicsContainer, None], Container[Element]):
    def definitions(self) -> Defs: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None: ...
