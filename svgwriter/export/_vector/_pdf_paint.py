"""
PDF and PostScript shadings read as SVG gradients, and PDF patterns as ``<pattern>`` paint servers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...transform.matrix import Matrix
from ._constants import AXIAL, EXPONENTIAL, IDENTITY_MATRIX, RADIAL, SHADING, STITCHING, TILING

if TYPE_CHECKING:
    from ...elements.core import Element
    from ._pdf_painter import _Painter

__all__ = ["fill_with_pattern", "gradient", "paint_shading", "pattern_paint"]


def _stops(objects: dict[Any, Any], function: Any, low: float = 0.0, high: float = 1.0) -> list[tuple[float, Any]] | None:
    """Gradient stops ``(offset, rgb)`` for an exponential or stitching function, offsets mapped to 0..1."""
    from ._pdf_objects import _resolve
    from ._pdf_painter import _color

    function = _resolve(objects, function)
    if isinstance(function, list):
        parts = [_stops(objects, f, low, high) for f in function]
        return parts[0] if parts and all(parts) else None
    info = function.info if hasattr(function, "info") else function
    if not isinstance(info, dict):
        return None
    kind = int(info.get("FunctionType", -1))
    if kind == EXPONENTIAL:
        start = _color(_resolve(objects, info.get("C0")) or [0.0])
        end = _color(_resolve(objects, info.get("C1")) or [1.0])
        return [(low, start), (high, end)]
    if kind == STITCHING:
        domain = [float(v) for v in _resolve(objects, info.get("Domain")) or [0, 1]]
        bounds = [float(v) for v in _resolve(objects, info.get("Bounds")) or []]
        edges = [domain[0], *bounds, domain[1]]
        span = (domain[1] - domain[0]) or 1.0
        stops: list[tuple[float, Any]] = []
        for part, (a, b) in zip(_resolve(objects, info.get("Functions")) or [], zip(edges, edges[1:], strict=False),
                                strict=False):
            piece = _stops(objects, part, low + (a - domain[0]) / span * (high - low),
                           low + (b - domain[0]) / span * (high - low))
            if piece is None:
                return None
            stops += piece if not stops else piece[1:] if stops[-1] == piece[0] else piece
        return stops or None
    return None


def gradient(objects: dict[Any, Any], shading: Any, matrix: Matrix) -> Element | None:
    """An axial or radial shading as a ``userSpaceOnUse`` gradient carrying *matrix*, or None if unsupported."""
    from ...color.color import Color
    from ...elements.paint import LinearGradient, RadialGradient, Stop
    from ._pdf_objects import _resolve

    info = shading.info if hasattr(shading, "info") else shading
    if not isinstance(info, dict):
        return None
    kind = int(info.get("ShadingType", 0))
    coords = [float(v) for v in _resolve(objects, info.get("Coords")) or []]
    stops = _stops(objects, info.get("Function"))
    if stops is None or kind not in (AXIAL, RADIAL) or len(coords) < (4 if kind == AXIAL else 6):
        return None
    children = [Stop(offset, Color(*rgb)) for offset, rgb in stops]
    if kind == AXIAL:
        made: Element = LinearGradient(*children, x1=coords[0], y1=coords[1], x2=coords[2], y2=coords[3],
                                       gradient_units="userSpaceOnUse")
    else:
        made = RadialGradient(*children, fx=coords[0], fy=coords[1], cx=coords[3], cy=coords[4], r=coords[5],
                              gradient_units="userSpaceOnUse")
    made.t = matrix  # type: ignore[attr-defined]
    return made


def paint_shading(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``sh``: fill the clip (or the whole page) with the named shading."""
    from ._reading import Shape, _path

    shading = painter.resource(resources, "Shading", operands[-1])
    paint = gradient(painter.objects, shading, painter.state.ctm) if shading is not None else None
    region = painter.state.clip or painter.page
    if paint is None or not region:
        return
    area = _path(Shape(region))
    area.set("fill", paint)
    area.set("stroke", "none")
    painter.shapes.append(area)


def pattern_paint(painter: _Painter, pattern: Any) -> Element | None:
    """A PDF pattern (shading or tiling) as an SVG paint server in page coordinates."""
    from ._pdf_objects import _resolve

    info = pattern.info if hasattr(pattern, "info") else pattern
    if not isinstance(info, dict):
        return None
    matrix = painter.base @ Matrix(*map(float, _resolve(painter.objects, info.get("Matrix")) or IDENTITY_MATRIX))
    kind = int(info.get("PatternType", 0))
    if kind == SHADING:
        return gradient(painter.objects, _resolve(painter.objects, info.get("Shading")), matrix)
    if kind == TILING and hasattr(pattern, "raw"):
        return _tiling(painter, pattern, matrix)
    return None


def _tiling(painter: _Painter, pattern: Any, matrix: Matrix) -> Element | None:
    """A tiling pattern's cell drawn by a nested painter into a ``<pattern>``."""
    from ...elements.paint import Pattern
    from ._pdf_objects import _decode, _resolve
    from ._pdf_painter import _Painter
    from ._reading import Shape, _path

    info = pattern.info
    box = [float(v) for v in _resolve(painter.objects, info.get("BBox")) or [0, 0, 1, 1]]
    step_x = float(info.get("XStep", box[2] - box[0])) or 1.0
    step_y = float(info.get("YStep", box[3] - box[1])) or 1.0
    inner = _Painter(painter.objects, Matrix())
    resources = _resolve(painter.objects, info.get("Resources"))
    inner.run(_decode(pattern), resources if isinstance(resources, dict) else {})
    cell = Pattern(x=box[0], y=box[1], width=abs(step_x), height=abs(step_y), pattern_units="userSpaceOnUse")
    for item in inner.shapes:
        cell.add(_path(item) if isinstance(item, Shape) else item)
    if not len(cell):
        return None
    cell.t = matrix
    return cell


def fill_with_pattern(painter: _Painter, ops: list[Any], evenodd: bool, stroke: bool) -> bool:
    """Paint *ops* with the current fill pattern; True when the pattern could be used."""
    from ._reading import Shape, _hex, _path

    paint = pattern_paint(painter, painter.state.fill_pattern)
    if paint is None:
        return False
    state = painter.state
    shape = _path(Shape(ops, evenodd=evenodd, clip=state.clip,
                        stroke=state.stroke if stroke else None, stroke_width=state.line_width))
    shape.set("fill", paint)
    if stroke:
        shape.set("stroke", _hex(state.stroke))
    if state.fill_alpha * state.group_alpha < 1:
        shape.set("fill-opacity", state.fill_alpha * state.group_alpha)
    if state.clip:
        shape.clip(_path(Shape(state.clip)))
    painter.shapes.append(shape)
    return True
