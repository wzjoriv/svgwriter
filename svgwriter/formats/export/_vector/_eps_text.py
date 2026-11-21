"""
PostScript fonts and ``show`` operators read into text.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ....model.transform.matrix import Matrix
from ._constants import DEFAULT_FONT, DEFAULT_TEXT_SIZE, STYLE_RE
from ._eps_syntax import _Font, _Underflow
from ._pdf_content import _clip
from ._reading import _hex

if TYPE_CHECKING:
    from ._eps_machine import _Machine

__all__: list[str] = []


def _find_font(machine: _Machine, _: int) -> None:
    """``findfont``: a font of one unit size under the given name."""
    machine.stack.append(_Font(machine.pop(1, str)[0], Matrix()))


def _scale_font(machine: _Machine, _: int) -> None:
    """``scalefont``: scale the font matrix."""
    font, size = machine.pop(2, object)
    machine.stack.append(_Font(font.name, Matrix.scale(size) @ font.matrix))


def _make_font(machine: _Machine, _: int) -> None:
    """``makefont``: transform the font matrix by a six-element matrix."""
    font, matrix = machine.pop(2, object)
    machine.stack.append(_Font(font.name, Matrix(*(float(v) for v in matrix[:6])) @ font.matrix))


def _select_font(machine: _Machine, _: int) -> None:
    """``selectfont``: a name with a size or a matrix, made the current font."""
    name, scale = machine.pop(2, object)
    matrix = Matrix.scale(scale) if isinstance(scale, float) else Matrix(*(float(v) for v in scale[:6]))
    machine.state.font = _Font(str(name), matrix)


def _set_font(machine: _Machine, _: int) -> None:
    """``setfont``: make a font current."""
    machine.state.font = machine.pop(1, _Font)[0]


def _move_current(machine: _Machine, x: float, y: float) -> None:
    """Set the current point to user coordinates (*x*, *y*) without adding a path segment."""
    outline = machine.outline
    point = tuple(machine.state.ctm.apply(x, y))
    if outline.ops and outline.ops[-1][0] == "M":
        outline.ops[-1] = ("M", point)
        outline.start = point
    outline.current = point


def _run(machine: _Machine, text: str) -> tuple[float, float]:
    """Draw *text* at the current point; the user-space advance of its measured width."""
    from ....model.elements.text import Text
    from ....ops.text import text_width

    current = machine.outline.user_current(machine.state.ctm)
    font = machine.state.font
    if current is None or font is None:
        raise _Underflow
    a, b, c, d, _, _ = font.matrix.as_tuple()
    size = math.sqrt(abs(a * d - b * c)) or DEFAULT_TEXT_SIZE
    unit = Matrix(a / size, b / size, c / size, d / size, 0.0, 0.0)
    style = font.name.lower()
    family = STYLE_RE.sub("", font.name) or DEFAULT_FONT
    bold, italic = "bold" in style, "italic" in style or "oblique" in style
    if text.strip():
        run = Text(text, x=0, y=0, font_size=size, font_family=family, fill=_hex(machine.state.color),
                   font_weight="bold" if bold else None, font_style="italic" if italic else None,
                   xml_space="preserve")
        run.t = machine.state.ctm @ Matrix.translate(*current) @ unit @ Matrix.scale(1, -1)
        if machine.state.clip:
            _clip(run, machine.state.clip)
        machine.shapes.append(run)
    width = text_width(text, family, size, weight="bold" if bold else "normal", italic=italic)
    return tuple(unit.apply(width, 0.0))


def _advance(machine: _Machine, dx: float, dy: float) -> None:
    """Move the current point by a user-space vector."""
    x, y = machine.outline.user_current(machine.state.ctm)
    _move_current(machine, x + dx, y + dy)


def _show_spaced(machine: _Machine, text: bytes, extras: list[tuple[float, float]]) -> None:
    """Show *text*, adding the user-space vector in *extras* after each character; one run when there are none."""
    string = text.decode("latin-1")
    if not any(extra != (0.0, 0.0) for extra in extras):
        _advance(machine, *_run(machine, string))
        return
    for char, (ex, ey) in zip(string, extras, strict=True):
        dx, dy = _run(machine, char)
        _advance(machine, dx + ex, dy + ey)


def _show(machine: _Machine, _: int) -> None:
    """``show``."""
    text = machine.pop(1, bytes)[0]
    _show_spaced(machine, text, [(0.0, 0.0)] * len(text))


def _ashow(machine: _Machine, _: int) -> None:
    """``ashow``: extra advance (ax, ay) after every character."""
    ax, ay, text = machine.pop(3, (float, bytes))
    if not isinstance(text, bytes):
        raise _Underflow
    _show_spaced(machine, text, [(ax, ay)] * len(text))


def _widthshow(machine: _Machine, _: int) -> None:
    """``widthshow``: extra advance (cx, cy) after each occurrence of one character code."""
    cx, cy, code, text = machine.pop(4, (float, bytes))
    if not isinstance(text, bytes):
        raise _Underflow
    _show_spaced(machine, text, [(cx, cy) if char == int(code) else (0.0, 0.0) for char in text])


def _awidthshow(machine: _Machine, _: int) -> None:
    """``awidthshow``: ``widthshow`` plus (ax, ay) after every character."""
    cx, cy, code, ax, ay, text = machine.pop(6, (float, bytes))
    if not isinstance(text, bytes):
        raise _Underflow
    _show_spaced(machine, text, [(ax + cx, ay + cy) if char == int(code) else (ax, ay) for char in text])


def _xyshow(machine: _Machine, _: int) -> None:
    """``xyshow``: the advance after each character is the (x, y) pair given for it."""
    text, offsets = machine.pop(2, (bytes, list))
    if not isinstance(text, bytes) or not isinstance(offsets, list):
        raise _Underflow
    for i, char in enumerate(text.decode("latin-1")):
        _run(machine, char)
        pair = offsets[2 * i:2 * i + 2]
        if len(pair) == 2:
            _advance(machine, *pair)
