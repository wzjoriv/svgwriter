"""
Graphs (networkx, igraph, rustworkx) drawn as editable SVG: nodes as circles, edges as lines or arcs, arrows and labels.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Hashable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ._constants import (
    ARROW_LENGTH,
    ARROW_SPREAD,
    EDGE_STROKE,
    EDGE_WIDTH,
    GRAPH_SIZE,
    LABEL_BASELINE,
    LABEL_SIZE,
    MARGIN,
    MUTUAL_BEND,
    NODE_FILL,
    NODE_RADIUS,
    NODE_STROKE,
)
from ._graph_adapters import ADAPTERS, GraphAdapter, adapter_for

if TYPE_CHECKING:
    from ..elements.structure import Group

__all__ = ["draw_graph", "is_graph"]

Layout = str | Mapping[Any, Any] | Sequence[Any] | Callable[..., Any]


def is_graph(value: object) -> bool:
    """Whether *value* is a networkx, igraph or rustworkx graph, checked without importing any of them.

    Parameters
    ----------
    value : object
        Anything.

    Returns
    -------
    bool
        True for a graph :func:`draw_graph` can draw.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.ops.graph.is_graph({"a": ["b"]})
    False
    """
    return adapter_for(value) is not None


def _points(raw: Any, keys: list[Hashable]) -> dict[Hashable, tuple[float, float]]:
    """Positions from a mapping ``{node: (x, y)}`` or a sequence of points in node order."""
    pairs = raw.items() if hasattr(raw, "items") else zip(keys, getattr(raw, "coords", raw), strict=False)
    positions = {node: (float(point[0]), float(point[1])) for node, point in pairs}
    missing = [node for node in keys if node not in positions]
    if missing:
        raise ValueError(f"the layout has no position for node(s) {', '.join(map(repr, missing[:3]))}")
    return positions


def _layout(adapter: GraphAdapter, graph: Any, keys: list[Hashable], layout: Layout,
            seed: int) -> dict[Hashable, tuple[float, float]]:
    if isinstance(layout, str):
        adapter.check(layout)
        return _points(adapter.layout(graph, layout, seed), keys)
    return _points(layout(graph) if callable(layout) else layout, keys)


def _fit(positions: dict[Any, tuple[float, float]], size: float) -> dict[Any, tuple[float, float]]:
    """Positions scaled into a ``size`` square with a margin, y pointing down."""
    xs, ys = [p[0] for p in positions.values()], [p[1] for p in positions.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    scale = (size - 2 * MARGIN) / span
    return {node: (MARGIN + (x - min(xs)) * scale, MARGIN + (max(ys) - y) * scale) for node, (x, y) in positions.items()}


def _attribute(data: Mapping[str, Any], key: str, default: Any) -> Any:
    value = data.get(key, default)
    return default if value is None else value


def draw_graph(graph: Any, *, layout: Layout = "spring", size: float = GRAPH_SIZE, labels: bool = True,
               edge_labels: bool = False, node_radius: float = NODE_RADIUS, node_fill: Any = NODE_FILL,
               edge_stroke: Any = EDGE_STROKE, edge_width: float = EDGE_WIDTH, seed: int = 0) -> Group:
    """Draw a networkx, igraph or rustworkx graph as SVG elements you can restyle afterwards.

    Nodes become ``<circle>`` elements (id ``node-<name>``), edges ``<line>``
    elements, or arcs when an edge runs both ways in a directed graph, with
    arrowheads for directed graphs, and labels ``<text>``. Per-node and
    per-edge attributes override the defaults: ``fill``, ``radius``,
    ``label``, ``stroke``, ``width``; an edge's ``label`` (or else its
    ``weight``) is written at its middle when *edge_labels*.

    Each library's own attributes are read: networkx node and edge data,
    igraph vertex and edge attributes (vertices keyed by ``name`` when set,
    else by index), and rustworkx payloads (a dict holds attributes; any
    other node payload is its label, any other edge payload its weight).

    Parameters
    ----------
    graph : networkx.Graph, igraph.Graph, rustworkx.PyGraph or rustworkx.PyDiGraph
        Directed or not; multigraphs are drawn as simple edges.
    layout : str, mapping, sequence or callable, optional
        A layout of the graph's own library: ``"spring"``, ``"circular"``,
        ``"kamada_kawai"`` and ``"random"`` work for all three, plus that
        library's others (networkx ``"spectral"``, igraph ``"sugiyama"``,
        rustworkx ``"spiral"``, ...). Or ready positions: ``{node: (x, y)}``,
        a library's own result (an igraph ``Layout``, a rustworkx
        ``Pos2DMapping``) or points in node order; or a function
        ``f(graph)`` returning any of these. Defaults to "spring".
    size : float, optional
        Side of the square the layout is fitted into. Defaults to 400.
    labels : bool, optional
        Write node names (or their ``label`` attribute). Defaults to True.
    edge_labels : bool, optional
        Write each edge's ``label`` or ``weight`` attribute at its middle.
        Defaults to False.
    node_radius, node_fill, edge_stroke, edge_width : optional
        Default node and edge style.
    seed : int, optional
        Seed for random layouts, so drawings are reproducible. Defaults to 0.

    Returns
    -------
    Group
        ``<g>`` with an edges group and a nodes group.

    Raises
    ------
    TypeError
        If *graph* is not a graph of a supported library.
    ValueError
        If the layout name is unknown to the graph's library, or positions
        are missing for some nodes.

    See Also
    --------
    svgwriter.Document.add : Takes graphs directly, drawn with the defaults.

    Notes
    -----
    Install a library with its extra: ``pysvgwriter[graph]`` (networkx),
    ``pysvgwriter[igraph]`` or ``pysvgwriter[rustworkx]``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> import networkx as nx  # doctest: +SKIP
    >>> picture = svg.ops.draw_graph(nx.path_graph(3), layout="circular")  # doctest: +SKIP
    >>> len([c for c in picture[1] if c.tag == "circle"])  # doctest: +SKIP
    3
    """
    from ..elements.structure import Group
    from ..elements.text import Text

    adapter = adapter_for(graph)
    if adapter is None:
        names = ", ".join(a.library for a in ADAPTERS)
        raise TypeError(f"draw_graph takes a {names} graph, not {type(graph).__name__}")
    data = adapter.read(graph)
    keys = list(data.nodes)
    positions = _fit(_layout(adapter, graph, keys, layout, seed), size) if keys else {}
    pairs = {(source, target) for source, target, _ in data.edges}
    picture = Group(class_="graph")
    edges = picture.group(class_="edges", stroke=edge_stroke, stroke_width=edge_width, fill="none")
    nodes = picture.group(class_="nodes", stroke=NODE_STROKE)
    radii = {node: float(_attribute(attrs, "radius", node_radius)) for node, attrs in data.nodes.items()}
    for source, target, attrs in data.edges:
        if source == target:
            continue
        (x1, y1), (x2, y2) = positions[source], positions[target]
        style = {"stroke": attrs.get("stroke"), "stroke_width": attrs.get("width")}
        bend = data.directed and (target, source) in pairs
        _edge(edges, (x1, y1), (x2, y2), radii[source], radii[target], data.directed, bend, style)
        text = attrs.get("label", attrs.get("weight")) if edge_labels else None
        if text is not None:
            edges.add(Text(f"{text:g}" if isinstance(text, float) else str(text), x=(x1 + x2) / 2,
                           y=(y1 + y2) / 2, font_size=LABEL_SIZE, text_anchor="middle", stroke="none",
                           fill=NODE_STROKE, class_="edge-label"))
    for node, attrs in data.nodes.items():
        x, y = positions[node]
        nodes.circle(x, y, radii[node], fill=_attribute(attrs, "fill", node_fill), id=f"node-{node}")
        if labels:
            nodes.add(Text(str(_attribute(attrs, "label", node)), x=x, y=y + LABEL_SIZE * LABEL_BASELINE,
                           font_size=LABEL_SIZE, text_anchor="middle", stroke="none", fill=NODE_STROKE))
    return picture


def _edge(group: Group, start: tuple[float, float], end: tuple[float, float], start_radius: float,
          end_radius: float, directed: bool, bend: bool, style: dict[str, Any]) -> None:
    """One edge from circle edge to circle edge, curved to one side when the reverse edge exists too."""
    (x1, y1), (x2, y2) = start, end
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    a = (x1 + ux * start_radius, y1 + uy * start_radius)
    b = (x2 - ux * end_radius, y2 - uy * end_radius)
    extra = {k: v for k, v in style.items() if v is not None}
    if bend:
        offset = length * MUTUAL_BEND
        control = ((a[0] + b[0]) / 2 - uy * offset, (a[1] + b[1]) / 2 + ux * offset)
        group.path(**extra).move_to(*a).quad_to(*control, *b)
        direction = (b[0] - control[0], b[1] - control[1])
    else:
        group.line(*a, *b, **extra)
        direction = (ux, uy)
    if directed:
        angle = math.atan2(direction[1], direction[0])
        spread = math.radians(ARROW_SPREAD)
        left = (b[0] - ARROW_LENGTH * math.cos(angle - spread), b[1] - ARROW_LENGTH * math.sin(angle - spread))
        right = (b[0] - ARROW_LENGTH * math.cos(angle + spread), b[1] - ARROW_LENGTH * math.sin(angle + spread))
        group.polygon([left, b, right], fill=extra.get("stroke", EDGE_STROKE), stroke="none")
