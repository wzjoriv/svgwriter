"""
Reading DXF, HPGL and G-code back into documents of paths.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

from ._constants import (
    ARC_STEP_DEGREES,
    DXF_POINT_FIELDS,
    DXF_VARIABLE,
    DXF_X,
    DXF_Y,
    GCODE_PAGE_RE,
    GCODE_WORD_RE,
    HEX_RE,
    HPGL_PENS,
    HPGL_RE,
    HPGL_UNITS_PER_MM,
    MAX_PAGE_MM,
    MM_PER_USER_UNIT,
)

if TYPE_CHECKING:
    from ....document import Document

__all__ = ["read_dxf", "read_gcode", "read_hpgl"]

Point = tuple[float, float]
Stroke = tuple[str, list[Point], bool]


def _document(strokes: list[Stroke], unit_mm: float, page: tuple[float, float] | None = None) -> Document:
    """Paths in user units with y pointing down.

    With the *page* size (mm) the file recorded, y flips about the page and the document
    takes its size, so svgwriter's own output reads back in place; otherwise y flips about
    the drawing's top and the document fits the drawing.
    """
    from ....document import Document
    from ....model.elements.shapes import Path

    drawn = [(color, points, closed) for color, points, closed in strokes if len(points) >= 2]
    top = page[1] if page else max((y for _, points, _ in drawn for _, y in points), default=0.0)
    doc = Document(page[0] / unit_mm, page[1] / unit_mm) if page else Document()
    for color, points, closed in drawn:
        path = Path(fill="none", stroke=color, stroke_width=0.5)
        path.move_to(points[0][0] / unit_mm, (top - points[0][1]) / unit_mm)
        for x, y in points[1:]:
            path.line_to(x / unit_mm, (top - y) / unit_mm)
        if closed:
            path.close()
        doc.add(path)
    return doc if page else doc.fit()


def _dxf_page(pairs: list[tuple[int, str]]) -> tuple[float, float] | None:
    """The ``$EXTMAX`` corner from the header when ``$EXTMIN`` is the origin (as svgwriter writes it)."""
    marks = {value: index for index, (code, value) in enumerate(pairs) if code == DXF_VARIABLE}

    def corner(name: str) -> tuple[float, float] | None:
        if name not in marks:
            return None
        fields = dict(pairs[marks[name] + 1:marks[name] + DXF_POINT_FIELDS])
        try:
            return float(fields[DXF_X]), float(fields[DXF_Y])
        except (KeyError, ValueError):
            return None

    low, high = corner("$EXTMIN"), corner("$EXTMAX")
    if low != (0.0, 0.0) or high is None or not all(0 < v < MAX_PAGE_MM for v in high):
        return None
    return high


def _arc(cx: float, cy: float, r: float, start: float, end: float) -> list[Point]:
    while end <= start:
        end += 360.0
    steps = max(1, math.ceil((end - start) / ARC_STEP_DEGREES))
    return [(cx + r * math.cos(math.radians(start + (end - start) * i / steps)),
             cy + r * math.sin(math.radians(start + (end - start) * i / steps))) for i in range(steps + 1)]


def _bulge(p: Point, q: Point, bulge: float) -> list[Point]:
    """Points along a DXF bulge arc from *p* to *q* (excluding *p*); positive bulge turns counter-clockwise."""
    chord = math.dist(p, q)
    if not bulge or not chord:
        return [q]
    sweep = 4 * math.atan(bulge)
    distance = chord / 2 / math.tan(sweep / 2)
    nx, ny = -(q[1] - p[1]) / chord, (q[0] - p[0]) / chord
    cx, cy = (p[0] + q[0]) / 2 + nx * distance, (p[1] + q[1]) / 2 + ny * distance
    radius = math.dist(p, (cx, cy))
    start = math.atan2(p[1] - cy, p[0] - cx)
    steps = max(1, math.ceil(abs(math.degrees(sweep)) / ARC_STEP_DEGREES))
    return [(cx + radius * math.cos(start + sweep * i / steps), cy + radius * math.sin(start + sweep * i / steps))
            for i in range(1, steps + 1)]


def _pairs(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    return [(int(lines[i].strip()), lines[i + 1].strip()) for i in range(0, len(lines) - 1, 2)]


def _entities(pairs: list[tuple[int, str]]) -> list[tuple[str, list[tuple[int, str]]]]:
    inside, current, entities = False, None, []
    for code, value in pairs:
        if code == 2 and value == "ENTITIES":
            inside = True
            continue
        if not inside:
            continue
        if code == 0:
            if value == "ENDSEC":
                break
            current = (value, [])
            entities.append(current)
        elif current is not None:
            current[1].append((code, value))
    return entities


def _color(layer: str) -> str:
    return f"#{layer.lower()}" if HEX_RE.match(layer) else "black"


def read_dxf(text: str, *, unit_mm: float = MM_PER_USER_UNIT) -> Document:
    """Read DXF ``LINE``, ``POLYLINE``, ``LWPOLYLINE`` (with bulges), ``CIRCLE``, ``ARC`` and ``ELLIPSE`` entities.

    Each entity becomes a stroked path, coloured from its layer name when that is a hex colour.

    Parameters
    ----------
    text : str
        The DXF text.
    unit_mm : float, optional
        Millimetres per user unit. Defaults to 25.4 / 96.

    Returns
    -------
    Document
        The drawing, y flipped to SVG's downward axis.

    See Also
    --------
    read_hpgl : Read plotter files.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._plotter._cnc import to_dxf
    >>> from svgwriter.formats.export._plotter._cnc_read import read_dxf
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> len(read_dxf(to_dxf(doc)))
    1
    """
    strokes: list[Stroke] = []
    polyline: tuple[str, list[Point], bool] | None = None
    pairs = _pairs(text)
    for kind, fields in _entities(pairs):
        values: dict[int, list[str]] = {}
        for code, value in fields:
            values.setdefault(code, []).append(value)

        def num(code: int, default: float = 0.0, values: dict[int, list[str]] = values) -> float:
            return float(values[code][0]) if code in values else default

        layer = _color(values.get(8, ["0"])[0])
        if kind == "LINE":
            strokes.append((layer, [(num(10), num(20)), (num(11), num(21))], False))
        elif kind == "CIRCLE":
            strokes.append((layer, _arc(num(10), num(20), num(40), 0.0, 360.0), True))
        elif kind == "ARC":
            strokes.append((layer, _arc(num(10), num(20), num(40), num(50), num(51)), False))
        elif kind == "ELLIPSE":
            cx, cy, mx, my, ratio = num(10), num(20), num(11), num(21), num(40, 1.0)
            start, end = num(41, 0.0), num(42, 2 * math.pi)
            steps = max(8, math.ceil(math.degrees(end - start) / ARC_STEP_DEGREES))
            points = []
            for i in range(steps + 1):
                t = start + (end - start) * i / steps
                points.append((cx + mx * math.cos(t) - my * ratio * math.sin(t),
                               cy + my * math.cos(t) + mx * ratio * math.sin(t)))
            strokes.append((layer, points, math.isclose(end - start, 2 * math.pi)))
        elif kind == "LWPOLYLINE":
            xs, ys = [float(v) for v in values.get(10, [])], [float(v) for v in values.get(20, [])]
            bulges = {}
            index = -1
            for code, value in fields:
                if code == 10:
                    index += 1
                elif code == 42:
                    bulges[index] = float(value)
            closed = int(num(70)) & 1 == 1
            vertices = list(zip(xs, ys, strict=False))
            points = vertices[:1]
            ring = vertices + vertices[:1] if closed else vertices
            for i in range(len(ring) - 1):
                points += _bulge(ring[i], ring[i + 1], bulges.get(i, 0.0))
            strokes.append((layer, points, closed))
        elif kind == "POLYLINE":
            polyline = (layer, [], int(num(70)) & 1 == 1)
        elif kind == "VERTEX" and polyline is not None:
            polyline[1].append((num(10), num(20)))
        elif kind == "SEQEND" and polyline is not None:
            strokes.append(polyline)
            polyline = None
    return _document(strokes, unit_mm, _dxf_page(pairs))


def read_hpgl(text: str, *, unit_mm: float = MM_PER_USER_UNIT) -> Document:
    """Read HPGL ``PU``/``PD``/``PA``/``PR``/``SP`` pen moves; pens use the standard colour palette.

    Parameters
    ----------
    text : str
        The HPGL text.
    unit_mm : float, optional
        Millimetres per user unit. Defaults to 25.4 / 96.

    Returns
    -------
    Document
        The drawing, with one stroked path per pen-down run.

    See Also
    --------
    read_dxf : Read CAD files.

    Examples
    --------
    >>> from svgwriter.formats.export._plotter._cnc_read import read_hpgl
    >>> len(read_hpgl("IN;SP1;PU0,0;PD400,0,400,400;PU;"))
    1
    """
    strokes: list[Stroke] = []
    pen, down, relative = 1, False, False
    x = y = 0.0
    current: list[Point] = []

    def flush() -> None:
        nonlocal current
        if len(current) > 1:
            strokes.append((HPGL_PENS.get(pen, "black"), current, False))
        current = []

    for command, args in HPGL_RE.findall(text.upper()):
        numbers = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+", args)]
        if command == "SP":
            flush()
            pen = int(numbers[0]) if numbers else 0
            continue
        if command in ("PU", "PD", "PA", "PR"):
            if command == "PU":
                flush()
                down = False
            elif command == "PD":
                down = True
            elif command in ("PA", "PR"):
                relative = command == "PR"
            for i in range(0, len(numbers) - 1, 2):
                nx, ny = numbers[i] / HPGL_UNITS_PER_MM, numbers[i + 1] / HPGL_UNITS_PER_MM
                x, y = (x + nx, y + ny) if relative else (nx, ny)
                if down:
                    if not current:
                        current = [(x, y)]
                    current.append((x, y))
                else:
                    current = [(x, y)]
            if down and not current:
                current = [(x, y)]
        elif command == "IN":
            flush()
            x = y = 0.0
    flush()
    return _document(strokes, unit_mm)


def read_gcode(text: str, *, unit_mm: float = MM_PER_USER_UNIT) -> Document:
    """Read G-code cutting moves (``G1``/``G2``/``G3`` while Z <= 0 or the laser is on) as paths.

    Inch programs (``G20``) are converted to millimetres.

    Parameters
    ----------
    text : str
        The G-code text.
    unit_mm : float, optional
        Millimetres per user unit. Defaults to 25.4 / 96.

    Returns
    -------
    Document
        The drawing, with one stroked path per cutting run.

    See Also
    --------
    read_hpgl : Read plotter files.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.formats.export._plotter._cnc import to_gcode
    >>> from svgwriter.formats.export._plotter._cnc_read import read_gcode
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.rect(0, 0, 10, 10, stroke="black", fill="none")
    >>> len(read_gcode(to_gcode(doc)))
    1
    """
    strokes: list[Stroke] = []
    x = y = 0.0
    z = 0.0
    laser = None
    scale = 1.0
    absolute = True
    motion = 0
    current: list[Point] = []

    def cutting() -> bool:
        return laser if laser is not None else z <= 0

    def flush() -> None:
        nonlocal current
        if len(current) > 1:
            strokes.append(("black", current, False))
        current = []

    for raw in text.splitlines():
        line = re.sub(r"\(.*?\)|;.*", "", raw).upper()
        words = GCODE_WORD_RE.findall(line)
        if not words:
            continue
        codes = {(letter, float(value)) for letter, value in words if letter in "GM"}
        params = {letter: float(value) for letter, value in words if letter not in "GMN"}
        for letter, value in codes:
            if letter == "G" and value in (0, 1, 2, 3):
                motion = int(value)
            elif letter == "G" and value == 20:
                scale = 25.4
            elif letter == "G" and value == 21:
                scale = 1.0
            elif letter == "G" and value in (90, 91):
                absolute = value == 90
            elif letter == "M" and value in (3, 4):
                laser = True
            elif letter == "M" and value == 5:
                laser = False
                flush()
        if "Z" in params:
            z = params["Z"] * scale if absolute else z + params["Z"] * scale
            if not cutting():
                flush()
        if "X" not in params and "Y" not in params:
            continue
        nx = params.get("X", x / scale) * scale if absolute else x + params.get("X", 0.0) * scale
        ny = params.get("Y", y / scale) * scale if absolute else y + params.get("Y", 0.0) * scale
        if motion == 0 or not cutting():
            flush()
            x, y = nx, ny
            continue
        if not current:
            current = [(x, y)]
        if motion in (2, 3) and ("I" in params or "J" in params):
            cx, cy = x + params.get("I", 0.0) * scale, y + params.get("J", 0.0) * scale
            a0 = math.degrees(math.atan2(y - cy, x - cx))
            a1 = math.degrees(math.atan2(ny - cy, nx - cx))
            if motion == 2:
                a0, a1 = a1, a0
            points = _arc(cx, cy, math.dist((x, y), (cx, cy)), a0, a1)
            current += (points[::-1] if motion == 2 else points)[1:]
        else:
            current.append((nx, ny))
        x, y = nx, ny
    flush()
    found = GCODE_PAGE_RE.search(text)
    return _document(strokes, unit_mm, (float(found[1]), float(found[2])) if found else None)
