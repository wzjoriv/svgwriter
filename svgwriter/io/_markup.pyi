from collections.abc import Iterator
from contextlib import contextmanager
from typing import IO, Any
from .._internal._typing import AnyPath
from ..elements.core._element import Element

__all__ = ["default_namespaces", "inline_content", "open_text", "ordered", "uses_xlink"]

def ordered(attributes: dict[str, Any]) -> list[tuple[str, Any]]: ...

def default_namespaces() -> dict[str, str]: ...

def inline_content(element: Element) -> bool: ...

def uses_xlink(element: Element) -> bool: ...

@contextmanager
def open_text(path: AnyPath, encoding: str) -> Iterator[IO[str]]: ...
