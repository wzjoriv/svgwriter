from typing import Any, TypeAlias
from ..elements.core import Element

__all__ = ["expand_markers", "vertices"]

Vertex: TypeAlias = tuple[float, float, float, float]

def vertices(data: Any) -> list[Vertex]: ...

def expand_markers(root: Element) -> None: ...
