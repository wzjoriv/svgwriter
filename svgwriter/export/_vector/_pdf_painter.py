"""
The PDF content painter: graphics state, path and colour operators, clipping and forms.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Final

from ...transform.matrix import Matrix
from ._constants import BLACK, CAP_NAMES, CLIP_TOLERANCE, HAIRLINE, JOIN_NAMES, PAINTS, PDF_MAX_DEPTH
from ._pdf_content import CONTENT_HANDLERS, draw_image
from ._pdf_objects import Name, Stream, _decode, _numbers, _operations, _resolve
from ._pdf_paint import fill_with_pattern, paint_shading
from ._reading import Outline, Shape, cmyk_to_rgb

if TYPE_CHECKING:
    from ._reading import RGB, Op

__all__: list[str] = []


@dataclass
class _State:
    """The PDF graphics state the reader tracks."""

    ctm: Matrix
    fill: RGB = BLACK
    stroke: RGB = BLACK
    fill_alpha: float = 1.0
    stroke_alpha: float = 1.0
    group_alpha: float = 1.0
    line_width: float = 1.0
    cap: int = 0
    join: int = 0
    miter: float = 4.0
    dashes: tuple[float, ...] = ()
    clip: list[Op] | None = None
    fill_pattern: Any = None


class _Painter:
    """Runs content streams, collecting painted shapes."""

    def __init__(self, objects: dict[int, Any], ctm: Matrix) -> None:
        self.objects = objects
        self.state = _State(ctm)
        self.saved: list[_State] = []
        self.outline = Outline()
        self.shapes: list[Any] = []
        self.depth = 0
        self.pending_clip: bool | None = None
        self.text_matrix = self.line_matrix = Matrix()
        self.leading = 0.0
        self.base = ctm
        self.page: list[Op] = []

    def run(self, content: bytes, resources: dict[str, Any]) -> None:
        """Execute *content* with *resources*; malformed operations are skipped."""
        for op, operands in _operations(content):
            handler = _HANDLERS.get(op)
            if handler is None:
                continue
            try:
                handler(self, operands, resources)
            except (ValueError, TypeError, IndexError, KeyError, ZeroDivisionError):
                continue

    def resource(self, resources: dict[str, Any], category: str, name: Any) -> Any:
        """The named entry of a resource category such as ``/ExtGState``."""
        table = _resolve(self.objects, resources.get(category)) or {}
        return _resolve(self.objects, table.get(name)) if isinstance(table, dict) else None

    def take(self) -> list[Op]:
        """The current path, ending it; a pending ``W``/``W*`` makes it (part of) the clip first."""
        ops = self.outline.take()
        if self.pending_clip is not None and ops:
            clip = _intersect(self.state.clip, ops)
            self.state.clip = None if _covers(clip, self.page) else clip
        self.pending_clip = None
        return ops

    def paint(self, fill: bool, stroke: bool, evenodd: bool) -> None:
        """Paint the current path and start a new one."""
        state, ops = self.state, self.take()
        if fill and state.fill_pattern is not None and ops and fill_with_pattern(self, ops, evenodd, stroke):
            return
        scale = math.sqrt(abs(state.ctm.determinant))
        self.shapes.append(Shape(
            ops, fill=state.fill if fill else None, stroke=state.stroke if stroke else None,
            fill_opacity=state.fill_alpha * state.group_alpha, stroke_opacity=state.stroke_alpha * state.group_alpha,
            evenodd=evenodd, stroke_width=state.line_width * scale if state.line_width > 0 else HAIRLINE,
            linecap=CAP_NAMES[state.cap % len(CAP_NAMES)], linejoin=JOIN_NAMES[state.join % len(JOIN_NAMES)],
            miter_limit=state.miter, dashes=tuple(d * scale for d in state.dashes), clip=state.clip))

    def form(self, xobject: Any, resources: dict[str, Any]) -> None:
        """Draw a Form XObject; a transparency group takes the current fill alpha as its opacity."""
        if isinstance(xobject, Stream) and xobject.info.get("Subtype") == "Image":
            draw_image(self, xobject)
            return
        if not (isinstance(xobject, Stream) and xobject.info.get("Subtype") == "Form") or self.depth >= PDF_MAX_DEPTH:
            return
        saved = self.state
        matrix = _resolve(self.objects, xobject.info.get("Matrix")) or [1, 0, 0, 1, 0, 0]
        self.state = replace(saved, ctm=saved.ctm @ Matrix(*map(float, matrix)))
        if "Group" in xobject.info:
            self.state = replace(self.state, group_alpha=saved.group_alpha * saved.fill_alpha,
                                 fill_alpha=1.0, stroke_alpha=1.0)
        inner = _resolve(self.objects, xobject.info.get("Resources"))
        self.depth += 1
        try:
            self.run(_decode(xobject), inner if isinstance(inner, dict) else resources)
        finally:
            self.depth -= 1
            self.state = saved


def _set_dash(state: _State, value: Any) -> None:
    """Set the dash array from ``[array phase]`` or a bare array; the phase is dropped."""
    pattern = value[0] if isinstance(value, list) and value and isinstance(value[0], list) else value
    state.dashes = tuple(float(v) for v in pattern) if isinstance(pattern, list) else ()


def _ext_gstate(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``gs``: alpha constants and line parameters from an ``/ExtGState`` dictionary."""
    entry = painter.resource(resources, "ExtGState", operands[-1])
    if not isinstance(entry, dict):
        return
    state = painter.state
    fields = {"CA": "stroke_alpha", "ca": "fill_alpha", "LW": "line_width", "ML": "miter"}
    for key, attribute in fields.items():
        if isinstance(entry.get(key), (int, float)):
            setattr(state, attribute, float(entry[key]))
    for key, attribute in (("LC", "cap"), ("LJ", "join")):
        if isinstance(entry.get(key), int):
            setattr(state, attribute, entry[key])
    if "D" in entry:
        _set_dash(state, _resolve(painter.objects, entry["D"]))


def _color(operands: list[Any]) -> RGB:
    """An RGB colour from 1 (gray), 3 (RGB) or 4 (CMYK) numeric operands, as in DeviceGray/RGB/CMYK."""
    values = [float(v) for v in operands if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(values) == 1:
        return (values[0],) * 3
    if len(values) == 3:
        return (values[0], values[1], values[2])
    if len(values) == 4:
        return cmyk_to_rgb(*values)
    raise ValueError("unsupported colour operands")


def _set_color(attribute: str, count: int | None) -> Callable[[_Painter, list[Any], dict[str, Any]], None]:
    """A handler setting the fill or stroke colour from *count* operands (any count when None)."""
    def handler(painter: _Painter, operands: list[Any], _: dict[str, Any]) -> None:
        setattr(painter.state, attribute, _color(operands[-count:] if count else operands))
        if attribute == "fill" and count:
            painter.state.fill_pattern = None
    return handler


def _fill_paint(painter: _Painter, operands: list[Any], resources: dict[str, Any]) -> None:
    """``scn``: a pattern name selects a pattern fill; numbers set a plain colour and clear the pattern."""
    if operands and isinstance(operands[-1], Name):
        painter.state.fill_pattern = painter.resource(resources, "Pattern", operands[-1])
        return
    painter.state.fill_pattern = None
    painter.state.fill = _color(operands)


def _fill_space(state: _State) -> None:
    """``cs``: a new fill colour space starts at black with no pattern."""
    state.fill = BLACK
    state.fill_pattern = None


def _paint(op: str) -> Callable[[_Painter, list[Any], dict[str, Any]], None]:
    """A handler for a path-painting operator such as ``f*`` or ``b``."""
    fill, stroke, evenodd, close = PAINTS[op]

    def handler(painter: _Painter, _: list[Any], __: dict[str, Any]) -> None:
        if close:
            painter.outline.close()
        painter.paint(fill, stroke, evenodd)
    return handler


def _restore(painter: _Painter) -> None:
    """``Q``: restore the saved graphics state, if any."""
    if painter.saved:
        painter.state = painter.saved.pop()


def _setter(attribute: str, convert: Callable[[float], Any]) -> Callable[[_Painter, list[Any], dict[str, Any]], None]:
    """A handler storing one number, converted, in a graphics-state field."""
    def handler(painter: _Painter, operands: list[Any], _: dict[str, Any]) -> None:
        setattr(painter.state, attribute, convert(_numbers(operands, 1)[0]))
    return handler


_HANDLERS: Final[dict[str, Callable[[_Painter, list[Any], dict[str, Any]], None]]] = {
    "m": lambda p, o, _: p.outline.move(p.state.ctm, *_numbers(o, 2)),
    "l": lambda p, o, _: p.outline.line(p.state.ctm, *_numbers(o, 2)),
    "c": lambda p, o, _: p.outline.curve(p.state.ctm, *_numbers(o, 6)),
    "v": lambda p, o, _: p.outline.curve(p.state.ctm, *(p.outline.user_current(p.state.ctm) or ()), *_numbers(o, 4)),
    "y": lambda p, o, _: p.outline.curve(p.state.ctm, *_numbers(o, 4), *_numbers(o, 2)),
    "h": lambda p, o, _: p.outline.close(),
    "re": lambda p, o, _: p.outline.rect(p.state.ctm, *_numbers(o, 4)),
    "n": lambda p, o, _: p.take(),
    **{op: _paint(op) for op in PAINTS},
    "q": lambda p, o, _: p.saved.append(replace(p.state)),
    "Q": lambda p, o, _: _restore(p),
    "cm": lambda p, o, _: setattr(p.state, "ctm", p.state.ctm @ Matrix(*_numbers(o, 6))),
    "w": _setter("line_width", float),
    "J": _setter("cap", int),
    "j": _setter("join", int),
    "M": _setter("miter", float),
    "d": lambda p, o, _: _set_dash(p.state, o[0] if o else []),
    "gs": _ext_gstate,
    "rg": _set_color("fill", 3), "RG": _set_color("stroke", 3),
    "g": _set_color("fill", 1), "G": _set_color("stroke", 1),
    "k": _set_color("fill", 4), "K": _set_color("stroke", 4),
    "sc": _set_color("fill", None), "scn": lambda p, o, r: _fill_paint(p, o, r),
    "sh": lambda p, o, r: paint_shading(p, o, r),
    "SC": _set_color("stroke", None), "SCN": _set_color("stroke", None),
    "cs": lambda p, o, _: _fill_space(p.state),
    "CS": lambda p, o, _: setattr(p.state, "stroke", BLACK),
    "Do": lambda p, o, r: p.form(p.resource(r, "XObject", o[-1]), r),
    **CONTENT_HANDLERS,
}


def _covers(clip: list[Op], page: list[Op]) -> bool:
    """Whether *clip* is one axis-aligned rectangle containing the whole *page*, so it clips nothing."""
    kinds = [op for op, _ in clip if op != "Z"]
    if not page or kinds[:1] != ["M"] or set(kinds[1:]) != {"L"} or len(kinds) not in (4, 5):
        return False
    points = [args for op, args in clip if op in ("M", "L")]
    xs, ys = {round(x, 6) for x, _ in points}, {round(y, 6) for _, y in points}
    if len(xs) != 2 or len(ys) != 2:
        return False
    page_points = [args for op, args in page if op in ("M", "L")]
    return (min(xs) <= min(x for x, _ in page_points) + CLIP_TOLERANCE
            and max(xs) >= max(x for x, _ in page_points) - CLIP_TOLERANCE
            and min(ys) <= min(y for _, y in page_points) + CLIP_TOLERANCE
            and max(ys) >= max(y for _, y in page_points) - CLIP_TOLERANCE)


def _intersect(current: list[Op] | None, ops: list[Op]) -> list[Op]:
    """The clip after intersecting *current* with the outline *ops* (both page-space operations)."""
    if current is None:
        return ops
    from ...ops.boolean import intersection
    from ._reading import _path

    return _operations_of(intersection(_path(Shape(current)).d, _path(Shape(ops)).d))


def _operations_of(data: Any) -> list[Op]:
    """Path data as ``M``/``L``/``C``/``Z`` operations."""
    from ...ops import from_skia, to_skia
    from ...pathdata.commands import ClosePath, CurveTo, LineTo, MoveTo, QuadTo

    ops: list[Op] = []
    here = (0.0, 0.0)
    for command in from_skia(to_skia(data)):
        if isinstance(command, MoveTo):
            here = (command.x, command.y)
            ops.append(("M", here))
        elif isinstance(command, LineTo):
            here = (command.x, command.y)
            ops.append(("L", here))
        elif isinstance(command, QuadTo):
            q, end = (command.x1, command.y1), (command.x, command.y)
            ops.append(("C", (here[0] + 2 / 3 * (q[0] - here[0]), here[1] + 2 / 3 * (q[1] - here[1]),
                              end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1]), *end)))
            here = end
        elif isinstance(command, CurveTo):
            here = (command.x, command.y)
            ops.append(("C", (command.x1, command.y1, command.x2, command.y2, *here)))
        elif isinstance(command, ClosePath):
            ops.append(("Z", ()))
    return ops
