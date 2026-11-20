from dataclasses import dataclass
from ...elements.structure import Group

__all__ = ["Flowchart", "parse_flowchart", "draw_flowchart"]

@dataclass
class Node:
    id: str
    label: str
    shape: str = 'rect'
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def __init__(
        self,
        id: str,
        label: str,
        shape: str = 'rect',
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
    ) -> None: ...

@dataclass
class Edge:
    source: str
    target: str
    label: str = ''
    style: str = 'solid'
    head: bool = True
    tail: bool = False

    def __init__(
        self,
        source: str,
        target: str,
        label: str = '',
        style: str = 'solid',
        head: bool = True,
        tail: bool = False,
    ) -> None: ...

@dataclass
class Flowchart:
    direction: str = 'TB'
    nodes: dict[str, Node] = ...
    edges: list[Edge] = ...
    subgraphs: list[tuple[str, list[str]]] = ...

    def __init__(
        self,
        direction: str = 'TB',
        nodes: dict[str, Node] = ...,
        edges: list[Edge] = ...,
        subgraphs: list[tuple[str, list[str]]] = ...,
    ) -> None: ...

def parse_flowchart(source: str) -> Flowchart: ...

def draw_flowchart(chart: Flowchart) -> Group: ...
