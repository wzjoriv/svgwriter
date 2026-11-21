"""
Polyline formats for CAD, plotters and CNC machines: DXF (R12), HPGL and G-code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..._internal._flat._flatten import Point, Scene, flatten, polylines
from ..._internal._numbers import format_number
from ._constants import DEFAULT_TOLERANCE, HPGL_UNITS_PER_MM, MM_PER_USER_UNIT, PRECISION

if TYPE_CHECKING:
    from ...document import Document
    from ...model.color.color import Color

__all__ = ["to_dxf", "to_gcode", "to_hpgl"]


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
    """AutoCAD DXF R12: one ``POLYLINE`` per subpath, in millimetres, y up, layer per colour.

    Parameters
    ----------
    document : Document
        The document to convert.
    tolerance : float, optional
        Maximum deviation (mm) when curves become line segments. Defaults to 0.05.
    unit_mm : float, optional
        Millimetres per user unit. Defaults to 25.4 / 96 (96 user units per inch).

    Returns
    -------
    str
        DXF text.

    See Also
    --------
    to_hpgl : Plotter output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._plotter._cnc import to_dxf
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> to_dxf(doc).count("POLYLINE")
    1
    """
    scene = flatten(document)
    lines = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4",
             "9", "$EXTMIN", "10", "0", "20", "0", "30", "0",
             "9", "$EXTMAX", "10", _n(scene.width * unit_mm), "20", _n(scene.height * unit_mm), "30", "0",
             "0", "ENDSEC",
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
    """HPGL for pen plotters and cutters: one pen per distinct colour (40 units/mm, y up).

    Parameters
    ----------
    document : Document
        The document to convert.
    tolerance : float, optional
        Maximum deviation (mm) when curves become line segments. Defaults to 0.05.
    unit_mm : float, optional
        Millimetres per user unit. Defaults to 25.4 / 96 (96 user units per inch).

    Returns
    -------
    str
        HPGL text.

    See Also
    --------
    to_gcode : Machine toolpaths.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._plotter._cnc import to_hpgl
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> to_hpgl(doc).splitlines()[:2]
    ['IN;', 'SP1;PU0,106;']
    """
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
    document : Document
        The document to convert.
    tolerance : float, optional
        Maximum deviation (mm) when curves become line segments. Defaults to 0.05.
    unit_mm : float, optional
        Millimetres per user unit (96 user units per inch by default). Defaults to 25.4 / 96.
    feed : float, optional
        Cutting feed rate in mm/min. Defaults to 1000.0.
    travel_z, cut_z : float, optional
        Tool heights for ``mode="mill"``. Default to 2.0 and -0.5.
    mode : {"mill", "laser"}, optional
        Raise and lower Z, or switch the laser with ``M3 S<power>``/``M5``. Defaults to "mill".
    power : float, optional
        Laser power for ``mode="laser"``. Defaults to 1000.0.

    Returns
    -------
    str
        G-code text.

    See Also
    --------
    to_dxf : CAD output.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._plotter._cnc import to_gcode
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> to_gcode(doc).splitlines()[:3]
    ['G21 (millimetres)', 'G90 (absolute)', 'G17']
    """
    scene = flatten(document)
    out = ["G21 (millimetres)", "G90 (absolute)", "G17",
           f"(page {_n(scene.width * unit_mm)} x {_n(scene.height * unit_mm)} mm)"]
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
