"""
Turning drawings into glyph outlines: painted area, overlap removal and contour direction.
"""

from __future__ import annotations

from typing import Any

from ..elements import Element, GraphicsContainer, PathOperand
from ..ops import from_skia, simplify, stroke_to_path, to_skia, union
from ..pathdata import ClosePath, CurveTo, LineTo, MoveTo, PathData, QuadTo

__all__ = ["draw_contours", "painted_outline"]

_NONE = "none"


def _painted(element: Element, name: str, default: str | None) -> bool:
    value = element.computed(name)
    value = default if value is None else str(value)
    return value is not None and value != _NONE


def painted_outline(shape: Element) -> PathData:
    """The area a drawing paints: filled outlines plus stroke outlines, overlaps merged.

    Parameters
    ----------
    shape : Element
        A shape, text, group or any element with an outline.

    Returns
    -------
    PathData
        Absolute ``M``/``L``/``Q``/``C``/``Z`` data in the drawing's coordinates.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.fonts._outline import painted_outline
    >>> painted_outline(svg.path("M0 0 H10", fill="none", stroke="black", stroke_width=2)).bbox
    BBox(x=0.0, y=-1.0, width=10.0, height=2.0)
    """
    parts = _parts(shape)
    return simplify(PathData(union(*parts) if len(parts) > 1 else parts[0]) if parts else PathData())


def _parts(element: Element) -> list[PathData]:
    if isinstance(element, GraphicsContainer):
        parts = [part for child in element if isinstance(child, Element) for part in _parts(child)]
        transform = getattr(element, "transform", None)
        return [part @ transform for part in parts] if transform is not None else parts
    if not isinstance(element, PathOperand):
        return []
    parts = []
    outline = element.outline()
    if _painted(element, "fill", "black"):
        parts.append(outline)
    if _painted(element, "stroke", None):
        width = float(element.computed("stroke-width") or 1)
        parts.append(stroke_to_path(outline, width, cap=str(element.computed("stroke-linecap") or "butt"),
                                    join=str(element.computed("stroke-linejoin") or "miter")))  # type: ignore[arg-type]
    return parts


def _contours(data: PathData) -> list[list[Any]]:
    contours: list[list[Any]] = []
    for command in data:
        if isinstance(command, MoveTo):
            contours.append([command])
        elif contours and not isinstance(command, ClosePath):
            contours[-1].append(command)
    return [contour for contour in contours if len(contour) > 1]


def _points(contour: list[Any]) -> list[tuple[float, float]]:
    points = []
    for command in contour:
        if isinstance(command, CurveTo):
            points += [(command.x1, command.y1), (command.x2, command.y2)]
        elif isinstance(command, QuadTo):
            points.append((command.x1, command.y1))
        points.append((command.x, command.y))
    return points


def _area(points: list[tuple[float, float]]) -> float:
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1], strict=True)) / 2


def _inside(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def draw_contours(data: PathData, pen: Any) -> None:
    """Draw y-up glyph data into a fontTools pen, outer contours counter-clockwise.

    Contour nesting decides direction (even depth is outer), which is what
    PostScript outlines expect; TrueType callers reverse it.

    Parameters
    ----------
    data : PathData
        Absolute ``M``/``L``/``Q``/``C``/``Z`` data in font units, y up, overlaps removed.
    pen : fontTools pen
        Receives ``moveTo``/``lineTo``/``qCurveTo``/``curveTo``/``closePath``.

    Examples
    --------
    >>> from fontTools.pens.recordingPen import RecordingPen
    >>> from svgwriter.fonts._outline import draw_contours
    >>> pen = RecordingPen()
    >>> draw_contours(PathData("M0 0 L0 10 L10 10 Z"), pen)
    >>> [operator for operator, _ in pen.value]
    ['moveTo', 'lineTo', 'lineTo', 'closePath']
    """
    from fontTools.pens.reverseContourPen import ReverseContourPen

    contours = _contours(from_skia(to_skia(data)))
    polygons = [_points(contour) for contour in contours]
    for index, contour in enumerate(contours):
        depth = sum(_inside(polygons[index][0], other) for spot, other in enumerate(polygons) if spot != index)
        clockwise = _area(polygons[index]) < 0
        target = ReverseContourPen(pen) if clockwise == (depth % 2 == 0) else pen
        _draw(contour, target)


def _draw(contour: list[Any], pen: Any) -> None:
    pen.moveTo((contour[0].x, contour[0].y))
    for command in contour[1:]:
        if isinstance(command, LineTo):
            pen.lineTo((command.x, command.y))
        elif isinstance(command, QuadTo):
            pen.qCurveTo((command.x1, command.y1), (command.x, command.y))
        elif isinstance(command, CurveTo):
            pen.curveTo((command.x1, command.y1), (command.x2, command.y2), (command.x, command.y))
    pen.closePath()
