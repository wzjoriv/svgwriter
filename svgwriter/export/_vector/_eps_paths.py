"""
PostScript path construction, clipping and graphics-state operators.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from ...model.transform.matrix import Matrix
from ._pdf_painter import _intersect
from ._reading import Outline

if TYPE_CHECKING:
    from ._eps_machine import _Machine

__all__: list[str] = []


def _arc(machine: _Machine, clockwise: bool) -> None:
    """``arc``/``arcn``: a circular arc about (x, y), joined to the current point by a line."""
    x, y, r, a1, a2 = machine.pop(5)
    start, end = math.radians(a1), math.radians(a2)
    sweep = (start - end) % (2 * math.pi) if clockwise else (end - start) % (2 * math.pi)
    if sweep == 0 and a1 != a2:
        sweep = 2 * math.pi
    machine.outline.arc(machine.state.ctm, (x, y), (r, r), start, -sweep if clockwise else sweep)


def _rectangle(machine: _Machine, fill: bool) -> None:
    """``rectfill``/``rectstroke``: paint a rectangle without touching the current path."""
    rect = Outline()
    rect.rect(machine.state.ctm, *machine.pop(4))
    machine.paint(fill, ops=rect.take())


def _setdash(machine: _Machine, _: int) -> None:
    """``setdash``: the dash array; the offset is dropped."""
    machine.pop(1)
    pattern = machine.pop(1, list)[0]
    machine.state.dashes = tuple(float(v) for v in pattern if isinstance(v, float))


def _grestore(machine: _Machine, _: int) -> None:
    """``grestore``: restore the saved state and path, if any."""
    if machine.saved:
        machine.state, machine.outline = machine.saved.pop()


def _gsave(machine: _Machine, _: int) -> None:
    """Save the graphics state, current path included."""
    machine.saved.append((replace(machine.state), machine.outline.copy()))


def _setter(attribute: str, convert: Callable[[float], Any]) -> Callable[[_Machine, int], None]:
    """An operator storing one number, converted, in a graphics-state field."""
    def operator(machine: _Machine, _: int) -> None:
        setattr(machine.state, attribute, convert(machine.pop(1)[0]))
    return operator


def _rotation(degrees: float) -> Matrix:
    """A rotation by *degrees* counter-clockwise in PostScript's y-up space."""
    cos, sin = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return Matrix(cos, sin, -sin, cos, 0.0, 0.0)


def _clip_to_path(machine: _Machine, _: int) -> None:
    """``clip``/``eoclip``: intersect the clip with the current path, which stays the current path."""
    ops = list(machine.outline.ops)
    if ops:
        machine.state.clip = _intersect(machine.state.clip, ops)


def _shfill(machine: _Machine, _: int) -> None:
    """``shfill``: fill the clip with an axial or radial shading dictionary, as a gradient."""
    from ._pdf_paint import gradient
    from ._reading import Shape, _path

    paint = gradient({}, machine.pop(1, dict)[0], machine.state.ctm)
    if paint is None or not machine.state.clip:
        return
    area = _path(Shape(machine.state.clip))
    area.set("fill", paint)
    area.set("stroke", "none")
    machine.shapes.append(area)
