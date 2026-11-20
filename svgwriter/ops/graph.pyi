from collections.abc import Callable, Mapping
from typing import Any
from ..elements.structure import Group

__all__ = ["draw_graph", "is_graph"]

def is_graph(value: object) -> bool: ...

def draw_graph(
    graph: Any,
    *,
    layout: str | Mapping[Any, Any] | Callable[..., Any] = 'spring',
    size: float = 400.0,
    labels: bool = True,
    node_radius: float = 12.0,
    node_fill: Any = '#4c9be8',
    edge_stroke: Any = '#555555',
    edge_width: float = 1.5,
    seed: int = 0,
) -> Group: ...
