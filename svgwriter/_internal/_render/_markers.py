"""
Markers drawn as geometry: each ``marker-start``/``-mid``/``-end`` becomes a placed copy of the marker's content.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from .._constants import (
    MARKABLE,
    MARKER_CLIP_ID,
    MARKER_DEFAULT_SIZE,
    MARKER_FREE,
    MARKER_PROPERTIES,
    MARKER_SHORTHAND,
    URL_OPEN,
    VISIBLE_OVERFLOW,
)
from .._tree import ancestors

if TYPE_CHECKING:
    from ...model.elements.core import Element
    from ...model.transform.matrix import Matrix

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
    >>> from svgwriter._internal._render._markers import vertices
    >>> [(x, y, i, o) for x, y, i, o in vertices(svg.PathData("M0 0 L10 0 L10 10"))]
    [(0.0, 0.0, 0.0, 0.0), (10.0, 0.0, 0.0, 90.0), (10.0, 10.0, 90.0, 90.0)]
    """
    from ...model.pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo
    from ...ops import from_skia, to_skia

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


def _number(marker: Element, name: str, default: float) -> float:
    from ...model.units.lengths import Length

    value = marker.get(name)
    return float(Length.parse(value).to_user_units()) if value is not None else default


def _content_matrix(marker: Element) -> Matrix:
    """The marker's ``viewBox`` mapped into its ``markerWidth`` by ``markerHeight`` viewport."""
    from ...model.attributes.viewbox import PreserveAspectRatio, ViewBox
    from ...model.transform.matrix import IDENTITY, Matrix
    from ._layers import fit_box

    box = marker.get("viewBox")
    if box is not None and not isinstance(box, ViewBox):
        box = ViewBox.parse(str(box))
    if box is None or not box.width or not box.height:
        return IDENTITY
    ratio = marker.get("preserveAspectRatio")
    ratio = ratio if isinstance(ratio, PreserveAspectRatio) else (
        PreserveAspectRatio.parse(str(ratio)) if ratio is not None else PreserveAspectRatio())
    return fit_box(_number(marker, "markerWidth", MARKER_DEFAULT_SIZE),
                   _number(marker, "markerHeight", MARKER_DEFAULT_SIZE),
                   box.width, box.height, ratio) @ Matrix.translate(-box.min_x, -box.min_y)


def _placement(marker: Element, x: float, y: float, angle: float, stroke_width: float) -> Matrix:
    """The marker viewport's space to the shape's space at one vertex, ``refX``/``refY`` on the vertex."""
    from ...model.transform.matrix import Matrix

    matrix = Matrix.translate(x, y) @ Matrix.rotate(angle)
    if str(marker.get("markerUnits") or "strokeWidth") == "strokeWidth":
        matrix = matrix @ Matrix.scale(stroke_width)
    ref_x, ref_y = _content_matrix(marker).apply(_number(marker, "refX", 0.0), _number(marker, "refY", 0.0))
    return matrix @ Matrix.translate(-ref_x, -ref_y)


def _instance(marker: Element, rules: list, serial: int) -> list[Element]:
    """The marker's content in its viewport, inheriting from the marker and clipped unless overflow shows it."""
    from ...model.attributes.cascade import INHERITED, computed
    from ...model.elements import ClipPath, Group, Rect

    content = Group(*(child.clone() for child in marker))
    for name in INHERITED - {*MARKER_PROPERTIES, MARKER_SHORTHAND}:
        value = computed(marker, name, None, rules)
        if value is not None:
            content.attributes[name] = value
    content.matrix = _content_matrix(marker)  # type: ignore[attr-defined]
    if str(computed(marker, "overflow", "hidden", rules)) in VISIBLE_OVERFLOW:
        return [content]
    clip = ClipPath(Rect(0, 0, _number(marker, "markerWidth", MARKER_DEFAULT_SIZE),
                         _number(marker, "markerHeight", MARKER_DEFAULT_SIZE)), id=f"{MARKER_CLIP_ID}{serial}")
    holder = Group(content)
    holder.attributes["clip-path"] = f"url(#{clip.id})"
    return [clip, holder]


def _marker_of(shape: Element, name: str, rules: list, ids: dict[str, Element]) -> Element | None:
    """The ``<marker>`` that property *name* puts on *shape*."""
    from ...model.attributes.cascade import computed
    from ...model.elements import Marker

    value = computed(shape, name, None, rules)
    marker = getattr(value, "element", None) or ids.get(str(value or "").strip()[len(URL_OPEN):-1])
    return marker if isinstance(marker, Marker) else None


def expand_markers(root: Element) -> None:
    """Replace the markers on paths, lines, polylines and polygons by placed copies of their content.

    Marker properties inherit (the ``marker`` shorthand is CSS only, so it is expanded by
    :func:`~svgwriter.model.attributes.cascade.resolve_styles` and ignored as an attribute), the content inherits from the ``<marker>`` (not the shape), and
    the content is clipped to the marker viewport unless its ``overflow`` shows it.

    Parameters
    ----------
    root : Element
        A render copy; it is changed in place.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._render._markers import expand_markers
    >>> doc = svg.Document(100, 20)
    >>> tip = doc.define(svg.Marker(svg.circle(0, 0, 2), orient="auto", overflow="visible"))
    >>> _ = doc.path("M10 10 L90 10", stroke="black", marker_end=tip)
    >>> copy = doc.root.clone()
    >>> expand_markers(copy)
    >>> [e.tag for e in copy if e.tag != "defs"]
    ['path', 'g']
    """
    from ...model.attributes.cascade import computed
    from ...model.attributes.rules import rules_of
    from ...model.elements import Group
    from ...model.units.lengths import Length

    rules = rules_of(root)
    ids = {str(e.get("id")): e for e in root.iter() if e.get("id")}
    shapes = [e for e in root.iter() if e.tag in MARKABLE and not any(a.tag in MARKER_FREE for a in ancestors(e))]
    serial = 0
    for shape in shapes:
        markers = [_marker_of(shape, name, rules, ids) for name in MARKER_PROPERTIES]
        if not any(markers):
            continue
        for name in (*MARKER_PROPERTIES, MARKER_SHORTHAND):
            shape.attributes.pop(name, None)
        points = vertices(shape.local_outline())  # type: ignore[attr-defined]
        try:
            stroke_width = float(Length.parse(computed(shape, "stroke-width", 1.0, rules)).to_user_units())
        except (TypeError, ValueError):
            stroke_width = 1.0
        placed = Group()
        placed.matrix = shape.matrix  # type: ignore[attr-defined]
        for name, marker, chosen in zip(MARKER_PROPERTIES, markers, (points[:1], points[1:-1], points[-1:]),
                                        strict=True):
            if marker is None:
                continue
            for x, y, incoming, outgoing in chosen:
                orient = str(marker.get("orient") or "0")
                if orient == "auto" or orient == "auto-start-reverse":
                    angle = outgoing if name == "marker-start" else incoming if name == "marker-end" else _bisect(
                        incoming, outgoing)
                    angle += 180 if orient == "auto-start-reverse" and name == "marker-start" else 0
                else:
                    angle = float(orient.removesuffix("deg"))
                serial += 1
                copy = Group(*_instance(marker, rules, serial))
                copy.matrix = _placement(marker, x, y, angle, stroke_width)
                placed.add(copy)
        parent = shape.parent
        if len(placed) and parent is not None:
            parent.insert(parent.children.index(shape) + 1, placed)
