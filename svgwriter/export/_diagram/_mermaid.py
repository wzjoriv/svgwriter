"""
Mermaid flowcharts without the Mermaid CLI: a parser for ``graph``/``flowchart`` and a layered layout.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._constants import (
    ARROW_LENGTH,
    ARROW_SPREAD,
    DIRECTIONS,
    EDGE_RE,
    EDGE_STROKE,
    FONT_SIZE,
    HEADER_RE,
    ID_RE,
    LABEL_BACKGROUND,
    MARGIN,
    NODE_FILL,
    NODE_GAP,
    NODE_STROKE,
    PADDING_X,
    PADDING_Y,
    RANK_GAP,
    SHAPES,
    SUBGRAPH_FILL,
    SUBGRAPH_STROKE,
    SWEEPS,
)

if TYPE_CHECKING:
    from ...document import Document
    from ...model.elements.structure import Group

__all__ = ["Flowchart", "parse_flowchart", "draw_flowchart"]


@dataclass
class Node:
    """A flowchart node: id, label, shape and, after layout, its centre and size."""

    id: str
    label: str
    shape: str = "rect"
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


@dataclass
class Edge:
    """A flowchart edge: ends, label and line style (``solid``, ``dotted``, ``thick``, ``invisible``)."""

    source: str
    target: str
    label: str = ""
    style: str = "solid"
    head: bool = True
    tail: bool = False


@dataclass
class Flowchart:
    """A parsed flowchart: direction, nodes in order of appearance, edges and subgraphs."""

    direction: str = "TB"
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    subgraphs: list[tuple[str, list[str]]] = field(default_factory=list)


def _node(chart: Flowchart, text: str) -> str | None:
    """Parse ``id``, ``id[label]``, ``id((label))``... adding or updating the node; returns its id."""
    text = text.strip().rstrip(";").strip()
    match = ID_RE.match(text)
    if match is None:
        return None
    node_id, rest = match.group(0), text[match.end():].strip()
    node = chart.nodes.setdefault(node_id, Node(node_id, node_id))
    for opening, closing, shape in SHAPES:
        if rest.startswith(opening) and rest.endswith(closing) and len(rest) >= len(opening) + len(closing):
            node.label = rest[len(opening):len(rest) - len(closing)].strip().strip('"')
            node.shape = shape
            break
    return node_id


def _edge_style(arrow: str) -> tuple[str, bool, bool]:
    style = "dotted" if "." in arrow else "thick" if "=" in arrow else "invisible" if arrow == "~~~" else "solid"
    head = arrow.endswith((">", "o", "x"))
    return style, head, arrow.startswith("<")


def parse_flowchart(source: str) -> Flowchart:
    """Parse Mermaid ``graph``/``flowchart`` source.

    Parameters
    ----------
    source : str
        The Mermaid text.

    Returns
    -------
    Flowchart
        Nodes, edges and subgraphs; styling directives (``classDef``,
        ``style``, ``click``, ``linkStyle``) are ignored.

    Raises
    ------
    ValueError
        If the text is not a flowchart.

    Examples
    --------
    >>> chart = parse_flowchart("graph LR\\n  A[Start] --> B{Ok?}\\n  B -->|yes| C((Done))")
    >>> chart.direction, [(n.id, n.label, n.shape) for n in chart.nodes.values()]
    ('LR', [('A', 'Start', 'rect'), ('B', 'Ok?', 'diamond'), ('C', 'Done', 'circle')])
    >>> [(e.source, e.target, e.label) for e in chart.edges]
    [('A', 'B', ''), ('B', 'C', 'yes')]
    """
    lines = [line.split("%%", 1)[0] for line in re.split(r"[\n;]", source)]
    lines = [line for line in lines if line.strip()]
    if not lines or (header := HEADER_RE.match(lines[0])) is None:
        raise ValueError("not a Mermaid flowchart: it must start with 'graph' or 'flowchart' and a direction")
    chart = Flowchart(DIRECTIONS[(header.group(1) or "TB").upper()])
    stack: list[tuple[str, list[str]]] = []
    for line in lines[1:]:
        text = line.strip()
        keyword = text.split(None, 1)[0].lower()
        if keyword in ("classdef", "class", "style", "click", "linkstyle", "direction"):
            continue
        if keyword == "subgraph":
            stack.append((text[len("subgraph"):].strip().strip('"') or f"group {len(chart.subgraphs) + 1}", []))
            continue
        if keyword == "end" and stack:
            chart.subgraphs.append(stack.pop())
            continue
        _statement(chart, text, stack)
    return chart


def _statement(chart: Flowchart, text: str, stack: list[tuple[str, list[str]]]) -> None:
    """One line: a node list or a chain ``a --> b -- label --> c`` with ``&`` groups."""
    parts = EDGE_RE.split(text)
    groups, links = [], []
    position = 0
    for match in EDGE_RE.finditer(text):
        groups.append(text[position:match.start()])
        arrow = match.group("arrow") or ("-->" if match.group("label2") is not None else
                                         "==>" if match.group("label3") is not None else "-.->")
        label = next((g for g in (match.group("label"), match.group("label2"), match.group("label3"),
                                  match.group("label4")) if g), "")
        links.append((arrow, label.strip().strip('"')))
        position = match.end()
    groups.append(text[position:])
    del parts
    ids = [[i for i in (_node(chart, piece) for piece in group.split("&")) if i] for group in groups]
    for node_ids in ids:
        for node_id in node_ids:
            if stack and node_id not in stack[-1][1]:
                stack[-1][1].append(node_id)
    for (arrow, label), sources, targets in zip(links, ids, ids[1:], strict=False):
        style, head, tail = _edge_style(arrow)
        for source in sources:
            for target in targets:
                chart.edges.append(Edge(source, target, label, style, head, tail))


def _measure(chart: Flowchart) -> None:
    from ...ops.text import text_width

    for node in chart.nodes.values():
        width = text_width(node.label, "sans-serif", FONT_SIZE) + 2 * PADDING_X
        height = FONT_SIZE + 2 * PADDING_Y
        if node.shape in ("circle", "double-circle"):
            width = height = max(width, height)
        elif node.shape == "diamond":
            width, height = width * 1.4, height * 1.6
        node.width, node.height = width, height


def _ranks(chart: Flowchart) -> dict[str, int]:
    """Longest-path layering after reversing the edges that close cycles (depth-first)."""
    order = list(chart.nodes)
    successors: dict[str, list[str]] = {n: [] for n in order}
    state: dict[str, int] = {}
    acyclic: list[tuple[str, str]] = []

    def visit(node: str) -> None:
        state[node] = 1
        for edge in chart.edges:
            if edge.source == node and edge.target != node:
                if state.get(edge.target) == 1:
                    acyclic.append((edge.target, node))
                else:
                    acyclic.append((node, edge.target))
                    if edge.target not in state:
                        visit(edge.target)
        state[node] = 2

    for node in order:
        if node not in state:
            visit(node)
    for source, target in set(acyclic):
        successors[source].append(target)
    rank = dict.fromkeys(order, 0)
    for _ in order:
        changed = False
        for source in order:
            for target in successors[source]:
                if rank[target] < rank[source] + 1:
                    rank[target], changed = rank[source] + 1, True
        if not changed:
            break
    return rank


def _order(chart: Flowchart, rank: dict[str, int]) -> list[list[str]]:
    """Nodes per rank, reordered by the barycentre of their neighbours to reduce crossings."""
    layers: list[list[str]] = [[] for _ in range(max(rank.values(), default=0) + 1)]
    for node in chart.nodes:
        layers[rank[node]].append(node)
    neighbours: dict[str, list[str]] = {n: [] for n in chart.nodes}
    for edge in chart.edges:
        neighbours[edge.source].append(edge.target)
        neighbours[edge.target].append(edge.source)
    for sweep in range(SWEEPS):
        indices = range(1, len(layers)) if sweep % 2 == 0 else range(len(layers) - 2, -1, -1)
        for index in indices:
            reference = layers[index - 1] if sweep % 2 == 0 else layers[index + 1]
            position = {node: i for i, node in enumerate(reference)}

            current = {node: i for i, node in enumerate(layers[index])}

            def centre(node: str, position: dict[str, int] = position, current: dict[str, int] = current) -> float:
                linked = [position[n] for n in neighbours[node] if n in position]
                return sum(linked) / len(linked) if linked else float(current[node])

            layers[index].sort(key=centre)
    return layers


def _place(chart: Flowchart, layers: list[list[str]]) -> None:
    """Centres from ranks and order, then rotated for the flowchart direction."""
    horizontal = chart.direction in ("LR", "RL")
    rank_offset = 0.0
    for layer in layers:
        nodes = [chart.nodes[n] for n in layer]
        depth = max((n.width if horizontal else n.height) for n in nodes) if nodes else 0.0
        span = sum((n.height if horizontal else n.width) for n in nodes) + NODE_GAP * max(len(nodes) - 1, 0)
        cursor = -span / 2
        for node in nodes:
            breadth = node.height if horizontal else node.width
            along, across = rank_offset + depth / 2, cursor + breadth / 2
            node.x, node.y = (along, across) if horizontal else (across, along)
            cursor += breadth + NODE_GAP
        rank_offset += depth + RANK_GAP
    if chart.direction in ("BT", "RL"):
        for node in chart.nodes.values():
            if chart.direction == "BT":
                node.y = rank_offset - RANK_GAP - node.y
            else:
                node.x = rank_offset - RANK_GAP - node.x


def _shape(node: Node) -> Any:
    from ...model.elements.shapes import Circle, Polygon, Rect

    x, y, w, h = node.x, node.y, node.width, node.height
    left, top, right, bottom = x - w / 2, y - h / 2, x + w / 2, y + h / 2
    style = {"fill": NODE_FILL, "stroke": NODE_STROKE, "stroke_width": 1}
    slant = h / 3
    polygons = {
        "diamond": [(x, top), (right, y), (x, bottom), (left, y)],
        "hexagon": [(left + slant, top), (right - slant, top), (right, y), (right - slant, bottom),
                    (left + slant, bottom), (left, y)],
        "parallelogram": [(left + slant, top), (right, top), (right - slant, bottom), (left, bottom)],
        "parallelogram-alt": [(left, top), (right - slant, top), (right, bottom), (left + slant, bottom)],
        "trapezoid": [(left + slant, top), (right - slant, top), (right, bottom), (left, bottom)],
        "trapezoid-alt": [(left, top), (right, top), (right - slant, bottom), (left + slant, bottom)],
        "flag": [(left, top), (right, top), (right, bottom), (left, bottom), (left + slant, y)],
    }
    if node.shape in polygons:
        return Polygon(polygons[node.shape], **style)
    if node.shape in ("circle", "double-circle"):
        return Circle(x, y, w / 2, **style)
    radius = {"round": 5.0, "stadium": h / 2, "cylinder": h / 4}.get(node.shape)
    return Rect(left, top, w, h, rx=radius, **style)


def _clip_to(node: Node, toward: tuple[float, float]) -> tuple[float, float]:
    """The point where the segment from the node centre toward *toward* leaves the node's box (or circle)."""
    dx, dy = toward[0] - node.x, toward[1] - node.y
    if not dx and not dy:
        return node.x, node.y
    if node.shape in ("circle", "double-circle"):
        scale = (node.width / 2) / math.hypot(dx, dy)
    elif node.shape == "diamond":
        scale = 1 / (abs(dx) / (node.width / 2) + abs(dy) / (node.height / 2))
    else:
        scale = min((node.width / 2) / abs(dx) if dx else math.inf, (node.height / 2) / abs(dy) if dy else math.inf)
    return node.x + dx * scale, node.y + dy * scale


def draw_flowchart(chart: Flowchart) -> Group:
    """Lay out and draw a parsed flowchart as a group of editable shapes, edges and labels."""
    from ...model.elements.structure import Group
    from ...model.elements.text import Text

    _measure(chart)
    _place(chart, _order(chart, _ranks(chart)))
    picture = Group(class_="flowchart", font_family="sans-serif", font_size=FONT_SIZE)
    boxes = picture.group(class_="subgraphs")
    edges = picture.group(class_="edges", fill="none", stroke=EDGE_STROKE)
    nodes = picture.group(class_="nodes")
    for title, members in chart.subgraphs:
        inside = [chart.nodes[m] for m in members if m in chart.nodes]
        if not inside:
            continue
        left = min(n.x - n.width / 2 for n in inside) - MARGIN
        top = min(n.y - n.height / 2 for n in inside) - MARGIN - FONT_SIZE
        right = max(n.x + n.width / 2 for n in inside) + MARGIN
        bottom = max(n.y + n.height / 2 for n in inside) + MARGIN
        boxes.rect(left, top, right - left, bottom - top, fill=SUBGRAPH_FILL, stroke=SUBGRAPH_STROKE)
        boxes.add(Text(title, x=(left + right) / 2, y=top + FONT_SIZE, text_anchor="middle"))
    for edge in chart.edges:
        if edge.style == "invisible" or edge.source not in chart.nodes or edge.target not in chart.nodes:
            continue
        source, target = chart.nodes[edge.source], chart.nodes[edge.target]
        start = _clip_to(source, (target.x, target.y))
        end = _clip_to(target, (source.x, source.y))
        width = 2.5 if edge.style == "thick" else 1.2
        dashes = "3 3" if edge.style == "dotted" else None
        edges.line(*start, *end, stroke_width=width, stroke_dasharray=dashes)
        for tip, base in ((end, start), (start, end)) if edge.tail else ((end, start),):
            if edge.head or tip is start:
                _arrow(edges, tip, base)
        if edge.label:
            mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            label = Text(edge.label, x=mid[0], y=mid[1] + FONT_SIZE * 0.35, text_anchor="middle", stroke="none",
                         fill=EDGE_STROKE, font_size=FONT_SIZE * 0.85)
            box = label.bounds()
            if box is not None:
                edges.rect(box.x - 3, box.y - 1, box.width + 6, box.height + 2, fill=LABEL_BACKGROUND, stroke="none")
            edges.add(label)
    for node in chart.nodes.values():
        nodes.add(_shape(node))
        if node.shape == "double-circle":
            nodes.circle(node.x, node.y, node.width / 2 + 4, fill="none", stroke=NODE_STROKE)
        nodes.add(Text(node.label, x=node.x, y=node.y + FONT_SIZE * 0.35, text_anchor="middle"))
    return picture


def _arrow(group: Group, tip: tuple[float, float], base: tuple[float, float]) -> None:
    angle = math.atan2(tip[1] - base[1], tip[0] - base[0])
    spread = math.radians(ARROW_SPREAD)
    points = [(tip[0] - ARROW_LENGTH * math.cos(angle - spread), tip[1] - ARROW_LENGTH * math.sin(angle - spread)),
              tip,
              (tip[0] - ARROW_LENGTH * math.cos(angle + spread), tip[1] - ARROW_LENGTH * math.sin(angle + spread))]
    group.polygon(points, fill=EDGE_STROKE, stroke="none")


def flowchart_document(source: str) -> Document:
    """A Mermaid flowchart laid out and drawn without the Mermaid CLI."""
    from ...document import Document

    doc = Document()
    doc.add(draw_flowchart(parse_flowchart(source)))
    return doc.fit(padding=MARGIN)
