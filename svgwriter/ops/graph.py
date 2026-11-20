"""
Graphs (networkx) drawn as editable SVG: nodes as circles, edges as lines or arcs, arrows and labels.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from ._constants import (
    ARROW_LENGTH,
    ARROW_SPREAD,
    EDGE_STROKE,
    EDGE_WIDTH,
    EXTRA_HINT,
    GRAPH_SIZE,
    LABEL_SIZE,
    LAYOUTS,
    MARGIN,
    NODE_FILL,
    NODE_RADIUS,
    NODE_STROKE,
)

if TYPE_CHECKING:
    from ..elements.structure import Group

__all__ = ["draw_graph", "is_graph"]


def is_graph(value: object) -> bool:
    """Whether *value* is a networkx graph (checked without importing networkx)."""
    return type(value).__module__.startswith("networkx") and hasattr(value, "adj") and hasattr(value, "nodes")


def _layout(graph: Any, layout: str | Mapping[Any, Any] | Callable[..., Any], seed: int) -> dict[Any, tuple[float, float]]:
    try:
        import networkx as nx
    except ImportError as error:
        raise ImportError(f"drawing graphs needs networkx; {EXTRA_HINT}") from error
    if isinstance(layout, Mapping):
        return {node: (float(x), float(y)) for node, (x, y) in layout.items()}
    if callable(layout):
        return {node: (float(x), float(y)) for node, (x, y) in layout(graph).items()}
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout {layout!r}; use one of {', '.join(LAYOUTS)}, a function or positions")
    function = getattr(nx, f"{layout}_layout")
    kwargs = {"seed": seed} if layout in ("spring", "random") else {}
    return {node: (float(x), float(y)) for node, (x, y) in function(graph, **kwargs).items()}


def _fit(positions: dict[Any, tuple[float, float]], size: float) -> dict[Any, tuple[float, float]]:
    """Positions scaled into a ``size`` square with a margin, y pointing down."""
    xs, ys = [p[0] for p in positions.values()], [p[1] for p in positions.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    scale = (size - 2 * MARGIN) / span
    return {node: (MARGIN + (x - min(xs)) * scale, MARGIN + (max(ys) - y) * scale) for node, (x, y) in positions.items()}


def _attribute(data: Mapping[str, Any], key: str, default: Any) -> Any:
    value = data.get(key, default)
    return default if value is None else value


def draw_graph(graph: Any, *, layout: str | Mapping[Any, Any] | Callable[..., Any] = "spring", size: float = GRAPH_SIZE,
               labels: bool = True, node_radius: float = NODE_RADIUS, node_fill: Any = NODE_FILL,
               edge_stroke: Any = EDGE_STROKE, edge_width: float = EDGE_WIDTH, seed: int = 0) -> Group:
    """Draw a networkx graph as SVG elements you can restyle afterwards.

    Nodes become ``<circle>`` elements (id ``node-<name>``), edges ``<line>``
    elements, or arcs when an edge runs both ways in a directed graph, with
    arrowheads for directed graphs, and labels ``<text>``. Per-node and
    per-edge attributes override the defaults: ``fill``, ``radius``,
    ``label``, ``stroke``, ``width``.

    Parameters
    ----------
    graph : networkx.Graph
        Any networkx graph (directed or not, multigraphs drawn as simple edges).
    layout : str, mapping or callable, optional
        A networkx layout name (``"spring"``, ``"circular"``, ``"kamada_kawai"``,
        ...), ready positions ``{node: (x, y)}``, or a function ``f(graph)``
        returning them. Defaults to "spring".
    size : float, optional
        Side of the square the layout is fitted into. Defaults to 400.
    labels : bool, optional
        Write node names (or their ``label`` attribute). Defaults to True.
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
    ImportError
        If networkx is not installed (``pip install 'pysvgwriter[graph]'``).
    ValueError
        If the layout name is unknown.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # import networkx as nx; doc = svg.Document(); doc.add(nx.karate_club_graph()); doc.fit()
    """
    from ..elements.structure import Group
    from ..elements.text import Text

    positions = _fit(_layout(graph, layout, seed), size) if len(graph) else {}
    directed = graph.is_directed()
    picture = Group(class_="graph")
    edges = picture.group(class_="edges", stroke=edge_stroke, stroke_width=edge_width, fill="none")
    nodes = picture.group(class_="nodes", stroke=NODE_STROKE)
    radii = {node: float(_attribute(data, "radius", node_radius)) for node, data in graph.nodes(data=True)}
    for source, target, data in graph.edges(data=True):
        if source == target:
            continue
        (x1, y1), (x2, y2) = positions[source], positions[target]
        style = {"stroke": data.get("stroke"), "stroke_width": data.get("width")}
        bend = directed and graph.has_edge(target, source)
        _edge(edges, (x1, y1), (x2, y2), radii[source], radii[target], directed, bend, style)
    for node, data in graph.nodes(data=True):
        x, y = positions[node]
        nodes.circle(x, y, radii[node], fill=_attribute(data, "fill", node_fill), id=f"node-{node}")
        if labels:
            nodes.add(Text(str(_attribute(data, "label", node)), x=x, y=y + LABEL_SIZE * 0.35, font_size=LABEL_SIZE,
                           text_anchor="middle", stroke="none", fill=NODE_STROKE))
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
        offset = length * 0.15
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
