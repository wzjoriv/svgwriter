from collections.abc import Callable
from typing import Concatenate, Generic, TypeVar, overload
from ._typing import P

__all__ = ["hybridmethod"]

S = TypeVar('S')

class hybridmethod(Generic[S, P]):
    func: Callable[Concatenate[S, P], object]

    def __init__(self, func: Callable[Concatenate[S, P], object]) -> None: ...
    @overload
    def __get__(self, obj: None, owner: type[S]) -> Callable[P, S]: ...
    @overload
    def __get__(self, obj: S, owner: type[S] | None = None) -> Callable[P, S]: ...
