"""Polyline formats for CAD, plotters and CNC machines: DXF (R12), HPGL and G-code."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Final, Literal

from .._internal._numbers import format_number
from ._flatten import Scene, flatten, to_cubic

if TYPE_CHECKING:
    from ..color.color import Color
    from ..document import Document

__all__ = ["polylines", "to_dxf", "to_gcode", "to_hpgl"]

MM_PER_USER_UNIT: Final = 25.4 / 96.0
DEFAULT_TOLERANCE: Final = 0.05
HPGL_UNITS_PER_MM: Final = 40.0
PRECISION: Final = 4
MAX_SEGMENTS: Final = 512

Point = tuple[float, float]


def polylines(data: object, tolerance: float) -> list[tuple[list[Point], bool]]:
    """Subpaths as point lists (curves subdivided to within *tolerance*), each with a closed flag."""
    result: list[tuple[list[Point], bool]] = []
    points: list[Point] = []
    current: Point = (0.0, 0.0)
    for op, args in to_cubic(data):  # type: ignore[arg-type]
        if op == "M":
            if len(points) > 1:
                result.append((points, False))
            current = (args[0], args[1])
            points = [current]
        elif op == "L":
            current = (args[0], args[1])
            points.append(current)
        elif op == "C":
            p0, p1, p2, p3 = current, (args[0], args[1]), (args[2], args[3]), (args[4], args[5])
            dd = max(math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
                     math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]))
            steps = min(MAX_SEGMENTS, max(1, math.ceil(math.sqrt(0.75 * dd / tolerance)))) if tolerance > 0 else 1
            for i in range(1, steps + 1):
                t = i / steps
                u = 1 - t
                points.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                               u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
            current = p3
        elif op == "Z" and points:
            if points[-1] != points[0]:
                points.append(points[0])
            result.append((points, True))
            current = points[0]
            points = [current]
    if len(points) > 1:
        result.append((points, False))
    return result


def _paths(scene: Scene, tolerance_units: float) -> list[tuple[Color | None, list[Point], bool]]:
    out = []
    for item in scene.items:
        color = item.stroke if item.stroke is not None else item.fill
        if item.stroke is None and item.fill is None:
            continue
        for points, closed in polylines(item.data, tolerance_units):
            out.append((color, points, closed))
    return out


def _n(value: float) -> str:
    return format_number(value, PRECISION)


def to_dxf(document: Document, *, tolerance: float = DEFAULT_TOLERANCE, unit_mm: float = MM_PER_USER_UNIT) -> str:
    """AutoCAD DXF R12: one ``POLYLINE`` per subpath, in millimetres, y up, layer per colour."""
    scene = flatten(document)
    lines = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
             "0", "SECTION", "2", "ENTITIES"]
    for color, points, closed in _paths(scene, tolerance / unit_mm):
        layer = color.hex[1:].upper() if color is not None else "0"
        lines += ["0", "POLYLINE", "8", layer, "66", "1", "70", "1" if closed else "0"]
        for x, y in points[:-1] if closed else points:
            lines += ["0", "VERTEX", "8", layer, "10", _n(x * unit_mm), "20", _n((scene.height - y) * unit_mm),
                      "30", "0"]
        lines += ["0", "SEQEND", "8", layer]
    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines) + "\n"


def to_hpgl(document: Document, *, tolerance: float = DEFAULT_TOLERANCE, unit_mm: float = MM_PER_USER_UNIT) -> str:
    """HPGL for pen plotters and cutters: one pen per distinct colour (40 units/mm, y up)."""
    scene = flatten(document)
    pens: dict[str, int] = {}
    scale = unit_mm * HPGL_UNITS_PER_MM
    commands = ["IN;"]
    for color, points, _ in _paths(scene, tolerance / unit_mm):
        key = color.hex if color is not None else "#000000"
        pens.setdefault(key, len(pens) + 1)
        coords = [(round(x * scale), round((scene.height - y) * scale)) for x, y in points]
        commands.append(f"SP{pens[key]};PU{coords[0][0]},{coords[0][1]};")
        commands.append("PD" + ",".join(f"{x},{y}" for x, y in coords[1:]) + ";")
    commands.append("PU;SP0;")
    return "\n".join(commands) + "\n"


def to_gcode(
    document: Document,
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    unit_mm: float = MM_PER_USER_UNIT,
    feed: float = 1000.0,
    travel_z: float = 2.0,
    cut_z: float = -0.5,
    mode: Literal["mill", "laser"] = "mill",
    power: float = 1000.0,
) -> str:
    """G-code toolpaths along every outline (millimetres, absolute, y up).

    Parameters
    ----------
    tolerance : float
        Maximum deviation (mm) when curves become line segments.
    unit_mm : float
        Millimetres per user unit (96 user units per inch by default).
    feed : float
        Cutting feed rate in mm/min.
    travel_z, cut_z : float
        Tool heights for ``mode="mill"``.
    mode : {"mill", "laser"}
        Raise and lower Z, or switch the laser with ``M3 S<power>``/``M5``.
    """
    scene = flatten(document)
    out = ["G21 (millimetres)", "G90 (absolute)", "G17"]
    up = ["M5"] if mode == "laser" else [f"G0 Z{_n(travel_z)}"]
    down = [f"M3 S{_n(power)}"] if mode == "laser" else [f"G1 Z{_n(cut_z)} F{_n(feed)}"]
    out += up
    for _, points, _ in _paths(scene, tolerance / unit_mm):
        x0, y0 = points[0]
        out.append(f"G0 X{_n(x0 * unit_mm)} Y{_n((scene.height - y0) * unit_mm)}")
        out += down
        out += [f"G1 X{_n(x * unit_mm)} Y{_n((scene.height - y) * unit_mm)} F{_n(feed)}" for x, y in points[1:]]
        out += up
    out += ["M2"]
    return "\n".join(out) + "\n"
