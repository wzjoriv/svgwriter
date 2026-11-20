"""
Markers drawn as geometry: each ``marker-start``/``-mid``/``-end`` becomes a placed copy of the marker's content.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from ._constants import MARKER_DEFAULT_SIZE, MARKER_PROPERTIES

if TYPE_CHECKING:
    from ..elements.core import Element
    from ..transform.matrix import Matrix

__all__ = ["expand_markers", "vertices"]

Vertex = tuple[float, float, float, float]


def _angle(dx: float, dy: float) -> float | None:
    return math.degrees(math.atan2(dy, dx)) if dx or dy else None


def vertices(data: Any) -> list[Vertex]:
    """The vertices of a path with their incoming and outgoing directions, for placing markers.

    Parameters
    ----------
    data : PathData
        The outline.

    Returns
    -------
    list of (x, y, incoming, outgoing)
        Each vertex with the direction (degrees) of the segment arriving at it
        and of the one leaving it; the first vertex reuses its outgoing
        direction as incoming and the last its incoming as outgoing.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._markers import vertices
    >>> [(x, y, i, o) for x, y, i, o in vertices(svg.PathData("M0 0 L10 0 L10 10"))]
    [(0.0, 0.0, 0.0, 0.0), (10.0, 0.0, 0.0, 90.0), (10.0, 10.0, 90.0, 90.0)]
    """
    from ..ops import from_skia, to_skia
    from ..pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo

    points: list[list[Any]] = []
    current = start = (0.0, 0.0)
    for command in from_skia(to_skia(data)):
        if isinstance(command, MoveTo):
            current = start = (command.x, command.y)
            points.append([*current, None, None])
            continue
        if isinstance(command, ClosePath):
            target, first, last = start, start, current
        elif isinstance(command, LineTo):
            target, first, last = (command.x, command.y), current, current
        elif isinstance(command, QuadTo):
            target, first, last = (command.x, command.y), (command.x1, command.y1), (command.x1, command.y1)
        elif isinstance(command, CurveTo):
            target, first, last = (command.x, command.y), (command.x1, command.y1), (command.x2, command.y2)
        else:
            continue
        leaving = _angle(first[0] - current[0], first[1] - current[1]) if first != current else None
        arriving = _angle(target[0] - last[0], target[1] - last[1]) if last != target else None
        leaving = leaving if leaving is not None else _angle(target[0] - current[0], target[1] - current[1])
        arriving = arriving if arriving is not None else leaving
        if points:
            points[-1][3] = leaving
        points.append([*target, arriving, None])
        current = target
    for point in points:
        point[2] = point[2] if point[2] is not None else point[3]
        point[3] = point[3] if point[3] is not None else point[2]
    return [(float(x), float(y), incoming or 0.0, outgoing or 0.0) for x, y, incoming, outgoing in points]


def _bisect(incoming: float, outgoing: float) -> float:
    turn = (outgoing - incoming + 180) % 360 - 180
    return incoming + turn / 2


def _placement(marker: Element, x: float, y: float, angle: float, stroke_width: float) -> Matrix:
    """Marker content space to the shape's space at one vertex."""
    from ..attributes.length import Length
    from ..attributes.viewbox import ViewBox
    from ..transform.matrix import Matrix

    def number(name: str, default: float) -> float:
        value = marker.get(name)
        return float(Length.parse(value).to_user_units()) if value is not None else default

    matrix = Matrix.translate(x, y) @ Matrix.rotate(angle)
    if str(marker.get("markerUnits") or "strokeWidth") == "strokeWidth":
        matrix = matrix @ Matrix.scale(stroke_width)
    box = marker.get("viewBox")
    if isinstance(box, str):
        box = ViewBox.parse(box)
    if box is not None and box.width and box.height:
        fit = min(number("markerWidth", MARKER_DEFAULT_SIZE) / box.width,
                  number("markerHeight", MARKER_DEFAULT_SIZE) / box.height)
        matrix = matrix @ Matrix.scale(fit)
    return matrix @ Matrix.translate(-number("refX", 0.0), -number("refY", 0.0))


def expand_markers(root: Element) -> None:
    """Replace the markers on paths, lines, polylines and polygons by placed copies of their content.

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._markers import expand_markers
    >>> doc = svg.Document(100, 20)
    >>> tip = doc.define(svg.Marker(svg.circle(0, 0, 2), orient="auto"))
    >>> _ = doc.path("M10 10 L90 10", stroke="black", marker_end=tip)
    >>> copy = doc.root.clone()
    >>> expand_markers(copy)
    >>> [e.tag for e in copy if e.tag != "defs"]
    ['path', 'g']
    """
    from ..attributes.cascade import computed, rules_of
    from ..attributes.length import Length
    from ..elements import Group, Marker

    rules = rules_of(root)
    ids = {str(e.get("id")): e for e in root.iter() if e.get("id")}
    shapes = [e for e in root.iter() if e.tag in ("path", "line", "polyline", "polygon")
              and any(e.get(name) is not None for name in MARKER_PROPERTIES)
              and not any(a.tag in ("marker", "defs", "clipPath", "mask", "pattern", "symbol") for a in _ancestors(e))]
    for shape in shapes:
        points = vertices(shape.local_outline())  # type: ignore[attr-defined]
        width = computed(shape, "stroke-width", 1.0, rules)
        try:
            stroke_width = float(Length.parse(width).to_user_units())
        except (TypeError, ValueError):
            stroke_width = 1.0
        placed = Group()
        placed.t = shape.t  # type: ignore[attr-defined]
        for name, chosen in zip(MARKER_PROPERTIES, (points[:1], points[1:-1], points[-1:]), strict=True):
            value = shape.attributes.pop(name, None)
            marker = getattr(value, "element", None) or ids.get(str(value or "").strip()[5:-1])
            if not isinstance(marker, Marker) or not points:
                continue
            for x, y, incoming, outgoing in chosen:
                orient = str(marker.get("orient") or "0")
                if orient == "auto" or orient == "auto-start-reverse":
                    angle = outgoing if name == "marker-start" else incoming if name == "marker-end" else _bisect(
                        incoming, outgoing)
                    angle += 180 if orient == "auto-start-reverse" and name == "marker-start" else 0
                else:
                    angle = float(orient.removesuffix("deg"))
                copy = Group(*(child.clone() for child in marker))
                copy.t = _placement(marker, x, y, angle, stroke_width)
                placed.add(copy)
        parent = shape.parent
        if len(placed) and parent is not None:
            parent.insert(parent.children.index(shape) + 1, placed)


def _ancestors(element: Element) -> list[Element]:
    chain, node = [], element.parent
    while node is not None:
        chain.append(node)
        node = node.parent
    return chain
