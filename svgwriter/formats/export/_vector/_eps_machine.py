"""
The PostScript interpreter core: graphics state, operand and dictionary stacks, operator table.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from ....model.transform.matrix import Matrix
from ._constants import BLACK, CAP_NAMES, HAIRLINE, JOIN_NAMES, MAX_STEPS, PS_MAX_DEPTH, SAVE_OBJECT
from ._eps_images import _colorimage, _filter, _image
from ._eps_paths import (
    _arc,
    _clip_to_path,
    _grestore,
    _gsave,
    _rectangle,
    _rotation,
    _setdash,
    _setter,
    _shfill,
)
from ._eps_syntax import Inline, Literal, Mark, Name, Procedure, _File, _Underflow
from ._eps_text import (
    _ashow,
    _awidthshow,
    _find_font,
    _make_font,
    _scale_font,
    _select_font,
    _set_font,
    _show,
    _widthshow,
    _xyshow,
)
from ._reading import Outline, Shape, cmyk_to_rgb

if TYPE_CHECKING:
    from ._eps_syntax import _Font
    from ._reading import RGB

__all__ = ["OPERATORS"]


@dataclass
class _State:
    """The PostScript graphics state the reader tracks; one colour serves fill and stroke."""

    ctm: Matrix
    color: RGB = BLACK
    line_width: float = 1.0
    cap: int = 0
    join: int = 0
    miter: float = 10.0
    dashes: tuple[float, ...] = ()
    font: _Font | None = None
    clip: list[tuple[str, tuple[float, ...]]] | None = None


class _Machine:
    """Executes a parsed program, collecting painted shapes."""

    def __init__(self, ctm: Matrix) -> None:
        self.stack: list[Any] = []
        self.dicts: list[dict[str, Any]] = [{}]
        self.state = _State(ctm)
        self.saved: list[tuple[_State, Outline]] = []
        self.outline = Outline()
        self.shapes: list[Any] = []
        self.file_data = b""
        self.steps = 0
        self.done = False

    def execute(self, program: list[Any], depth: int = 0) -> None:
        """Push literals and call names in *program*; stops at ``showpage`` or the step limit."""
        for item in program:
            if self.done or self.steps >= MAX_STEPS:
                return
            self.steps += 1
            if isinstance(item, Name):
                self.call(item, depth)
            elif isinstance(item, Inline):
                self.file_data = bytes(item)
            else:
                self.stack.append(item)

    def call(self, name: str, depth: int) -> None:
        """Run a user definition or a built-in operator; unknown names are ignored."""
        found, value = self.lookup(name)
        if found:
            if isinstance(value, (Procedure, Name)) and depth < PS_MAX_DEPTH:
                self.execute(value if isinstance(value, Procedure) else [value], depth + 1)
            elif not isinstance(value, (Procedure, Name)):
                self.stack.append(value)
            return
        operator = OPERATORS.get(name)
        if operator is None:
            return
        try:
            operator(self, depth)
        except (_Underflow, ValueError, ZeroDivisionError, OverflowError, TypeError, AttributeError):
            return

    def lookup(self, name: str) -> tuple[bool, Any]:
        """Whether *name* is defined on the dictionary stack, and its value from the innermost definition."""
        for names in reversed(self.dicts):
            if name in names:
                return True, names[name]
        return False, None

    def pop(self, count: int = 1, kind: type | tuple[type, ...] = float) -> list[Any]:
        """The top *count* operands; on too few or a wrong type they are dropped and the operator skipped."""
        values = self.stack[-count:] if count <= len(self.stack) else None
        del self.stack[-count:]
        if values is None or not all(isinstance(v, kind) for v in values):
            raise _Underflow
        return values

    def paint(self, fill: bool, evenodd: bool = False, ops: list | None = None) -> None:
        """Paint *ops* (the current path, consumed, when None) with the current colour."""
        state = self.state
        ops = self.outline.take() if ops is None else ops
        scale = math.sqrt(abs(state.ctm.determinant))
        self.shapes.append(Shape(
            ops, fill=state.color if fill else None, stroke=None if fill else state.color, evenodd=evenodd,
            stroke_width=state.line_width * scale if state.line_width > 0 else HAIRLINE, linecap=CAP_NAMES[state.cap % len(CAP_NAMES)],
            linejoin=JOIN_NAMES[state.join % len(JOIN_NAMES)], miter_limit=state.miter,
            dashes=tuple(d * scale for d in state.dashes), clip=state.clip))

    def relative(self, *offsets: float) -> list[float]:
        """Absolute user coordinates of *offsets* (x, y pairs) from the current point."""
        current = self.outline.user_current(self.state.ctm)
        if current is None:
            raise _Underflow
        return [v + current[i % 2] for i, v in enumerate(offsets)]

    def transform(self, matrix: Matrix) -> None:
        """Concatenate *matrix* to the current transform."""
        self.state.ctm = self.state.ctm @ matrix


def _def(machine: _Machine, _: int) -> None:
    """``def``: bind a literal name to a value in the innermost dictionary."""
    value = machine.pop(1, object)[0]
    machine.dicts[-1][machine.pop(1, Literal)[0]] = value


def _load(machine: _Machine, _: int) -> None:
    """``load``: push a name's value, or the executable name of a built-in operator."""
    name = machine.pop(1, Literal)[0]
    found, value = machine.lookup(name)
    machine.stack.append(value if found else Name(name))


def _exec(machine: _Machine, depth: int) -> None:
    """``exec``: run a procedure or executable name from the stack."""
    value = machine.pop(1, object)[0]
    if isinstance(value, Procedure) and depth < PS_MAX_DEPTH:
        machine.execute(value, depth + 1)
    elif isinstance(value, Name):
        machine.call(value, depth + 1)


def _to_mark(machine: _Machine) -> list[Any]:
    """Pop the operands above the topmost mark, and the mark."""
    marks = [i for i, v in enumerate(machine.stack) if isinstance(v, Mark)]
    if not marks:
        raise _Underflow
    items = machine.stack[marks[-1] + 1:]
    del machine.stack[marks[-1]:]
    return items


def _close_dict(machine: _Machine, _: int) -> None:
    """``>>``: a dictionary from the key-value pairs above the mark."""
    items = _to_mark(machine)
    machine.stack.append({k: v for k, v in zip(items[::2], items[1::2], strict=False) if isinstance(k, Literal)})


def _begin(machine: _Machine, _: int) -> None:
    """``begin``: push a dictionary onto the dictionary stack."""
    machine.dicts.append(machine.pop(1, dict)[0])


def _end(machine: _Machine, _: int) -> None:
    """``end``: pop the dictionary stack, never the outermost dictionary."""
    if len(machine.dicts) > 1:
        machine.dicts.pop()


def _binary(function: Callable[[float, float], float]) -> Callable[[_Machine, int], None]:
    """An arithmetic operator applying *function* to the top two numbers."""
    def operator(machine: _Machine, _: int) -> None:
        a, b = machine.pop(2)
        machine.stack.append(float(function(a, b)))
    return operator


OPERATORS: Final[dict[str, Callable[[_Machine, int], None]]] = {
    "clip": _clip_to_path,
    "eoclip": _clip_to_path,
    "shfill": _shfill,
    "image": _image,
    "colorimage": _colorimage,
    "currentfile": lambda m, _: m.stack.append(_File()),
    "filter": _filter,
    "true": lambda m, _: m.stack.append(True),
    "false": lambda m, _: m.stack.append(False),
    "findfont": _find_font,
    "scalefont": _scale_font,
    "makefont": _make_font,
    "selectfont": _select_font,
    "setfont": _set_font,
    "show": _show,
    "ashow": _ashow,
    "widthshow": _widthshow,
    "awidthshow": _awidthshow,
    "xyshow": _xyshow,
    "moveto": lambda m, _: m.outline.move(m.state.ctm, *m.pop(2)),
    "lineto": lambda m, _: m.outline.line(m.state.ctm, *m.pop(2)),
    "curveto": lambda m, _: m.outline.curve(m.state.ctm, *m.pop(6)),
    "rmoveto": lambda m, _: m.outline.move(m.state.ctm, *m.relative(*m.pop(2))),
    "rlineto": lambda m, _: m.outline.line(m.state.ctm, *m.relative(*m.pop(2))),
    "rcurveto": lambda m, _: m.outline.curve(m.state.ctm, *m.relative(*m.pop(6))),
    "closepath": lambda m, _: m.outline.close(),
    "newpath": lambda m, _: m.outline.take(),
    "arc": lambda m, _: _arc(m, clockwise=False),
    "arcn": lambda m, _: _arc(m, clockwise=True),
    "fill": lambda m, _: m.paint(True),
    "eofill": lambda m, _: m.paint(True, evenodd=True),
    "stroke": lambda m, _: m.paint(False),
    "rectfill": lambda m, _: _rectangle(m, fill=True),
    "rectstroke": lambda m, _: _rectangle(m, fill=False),
    "showpage": lambda m, _: setattr(m, "done", True),
    "setrgbcolor": lambda m, _: setattr(m.state, "color", tuple(m.pop(3))),
    "setgray": lambda m, _: setattr(m.state, "color", (m.pop(1)[0],) * 3),
    "setcmykcolor": lambda m, _: setattr(m.state, "color", cmyk_to_rgb(*m.pop(4))),
    "setlinewidth": _setter("line_width", float),
    "setlinecap": _setter("cap", int),
    "setlinejoin": _setter("join", int),
    "setmiterlimit": _setter("miter", float),
    "setdash": _setdash,
    "gsave": _gsave,
    "grestore": _grestore,
    "save": lambda m, d: (_gsave(m, d), m.stack.append(SAVE_OBJECT)),
    "restore": lambda m, d: (m.pop(1, object), _grestore(m, d)),
    "translate": lambda m, _: m.transform(Matrix.translate(*m.pop(2))),
    "scale": lambda m, _: m.transform(Matrix.scale(*m.pop(2))),
    "rotate": lambda m, _: m.transform(_rotation(m.pop(1)[0])),
    "concat": lambda m, _: m.transform(Matrix(*(float(v) for v in m.pop(1, list)[0][:6]))),
    "dup": lambda m, _: m.stack.extend(m.pop(1, object) * 2),
    "pop": lambda m, _: m.pop(1, object),
    "exch": lambda m, _: m.stack.extend(m.pop(2, object)[::-1]),
    "add": _binary(lambda a, b: a + b),
    "sub": _binary(lambda a, b: a - b),
    "mul": _binary(lambda a, b: a * b),
    "div": _binary(lambda a, b: a / b),
    "neg": lambda m, _: m.stack.append(-m.pop(1)[0]),
    "def": _def,
    "bind": lambda m, _: None,
    "load": _load,
    "exec": _exec,
    "[": lambda m, _: m.stack.append(Mark()),
    "]": lambda m, _: m.stack.append(_to_mark(m)),
    "<<": lambda m, _: m.stack.append(Mark()),
    ">>": _close_dict,
    "dict": lambda m, _: (m.pop(1), m.stack.append({})),
    "begin": _begin,
    "end": _end,
    "currentdict": lambda m, _: m.stack.append(m.dicts[-1]),
}
