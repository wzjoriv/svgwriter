"""
Graph adapters: one per graph library, each reading nodes, edges and layouts into one plain form.
"""

from __future__ import annotations

import importlib
import random
from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from ._constants import GRAPH_LAYOUTS, GRAPH_TYPES, IGRAPH_LAYOUT_NAMES, SEEDED_LAYOUTS

__all__ = ["ADAPTERS", "GraphAdapter", "GraphData", "adapter_for"]


@dataclass(frozen=True)
class GraphData:
    """A graph read into plain Python: node attributes by key, edges as ``(source, target, attributes)``."""

    nodes: dict[Hashable, Mapping[str, Any]]
    edges: list[tuple[Hashable, Hashable, Mapping[str, Any]]]
    directed: bool


class GraphAdapter:
    """Reads one library's graphs; recognised by module name and shape, so the library is never imported early."""

    library: ClassVar[str]

    @property
    def layouts(self) -> tuple[str, ...]:
        """Layout names this library offers."""
        return GRAPH_LAYOUTS[self.library]

    def matches(self, value: object) -> bool:
        """Whether *value* is a graph of this library."""
        return (type(value).__module__.split(".")[0] == self.library
                and all(hasattr(value, name) for name in GRAPH_TYPES[self.library]))

    def read(self, graph: Any) -> GraphData:
        """Nodes, edges and direction of *graph*."""
        raise NotImplementedError

    def layout(self, graph: Any, name: str, seed: int) -> Any:
        """Positions from the library's own layout *name* (a mapping, or a sequence in node order)."""
        raise NotImplementedError

    def check(self, name: str) -> None:
        """Raise a ``ValueError`` naming the choices when *name* is not one of :attr:`layouts`."""
        if name not in self.layouts:
            raise ValueError(f"unknown {self.library} layout {name!r}; use one of {', '.join(self.layouts)}, "
                             "positions {node: (x, y)} or a function f(graph) returning them")


class NetworkxAdapter(GraphAdapter):
    """networkx ``Graph``, ``DiGraph`` and multigraphs (drawn as simple edges)."""

    library = "networkx"

    def read(self, graph: Any) -> GraphData:
        return GraphData(dict(graph.nodes(data=True)), list(graph.edges(data=True)), graph.is_directed())

    def layout(self, graph: Any, name: str, seed: int) -> Any:
        function = getattr(importlib.import_module(self.library), f"{name}_layout")
        return function(graph, **({"seed": seed} if name in SEEDED_LAYOUTS else {}))


class IgraphAdapter(GraphAdapter):
    """python-igraph ``Graph``; vertices are keyed by their ``name`` attribute when present, else by index."""

    library = "igraph"

    @staticmethod
    def _keys(graph: Any) -> list[Hashable]:
        return list(graph.vs["name"]) if "name" in graph.vs.attributes() else list(range(graph.vcount()))

    def read(self, graph: Any) -> GraphData:
        keys = self._keys(graph)
        nodes = {key: vertex.attributes() for key, vertex in zip(keys, graph.vs, strict=True)}
        edges = [(keys[edge.source], keys[edge.target], edge.attributes()) for edge in graph.es]
        return GraphData(nodes, edges, graph.is_directed())

    def layout(self, graph: Any, name: str, seed: int) -> Any:
        state = random.getstate()
        random.seed(seed)
        try:
            coords = graph.layout(IGRAPH_LAYOUT_NAMES.get(name, name)).coords
        finally:
            random.setstate(state)
        return dict(zip(self._keys(graph), coords, strict=False))


class RustworkxAdapter(GraphAdapter):
    """rustworkx ``PyGraph`` and ``PyDiGraph``; a dict payload holds attributes, any other is a label or weight."""

    library = "rustworkx"

    def read(self, graph: Any) -> GraphData:
        nodes = {index: _payload(graph[index], "label") for index in graph.node_indices()}
        edges = [(source, target, _payload(data, "weight")) for source, target, data in graph.weighted_edge_list()]
        return GraphData(nodes, edges, type(graph).__name__ == "PyDiGraph")

    def layout(self, graph: Any, name: str, seed: int) -> Any:
        function = getattr(importlib.import_module(self.library), f"{name}_layout")
        return function(graph, **({"seed": seed} if name in SEEDED_LAYOUTS else {}))


def _payload(data: Any, key: str) -> Mapping[str, Any]:
    if isinstance(data, Mapping):
        return data
    return {} if data is None else {key: data}


ADAPTERS: tuple[GraphAdapter, ...] = (NetworkxAdapter(), IgraphAdapter(), RustworkxAdapter())


def adapter_for(value: object) -> GraphAdapter | None:
    """The adapter that reads *value*, or None when it is not a graph of a supported library."""
    return next((adapter for adapter in ADAPTERS if adapter.matches(value)), None)
