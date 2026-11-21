"""
TikZ scopes, coordinate frames, statement events and unrolled foreach loops.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from ...model.transform.matrix import IDENTITY, Matrix
from ._constants import (
    DEFAULT_UNIT,
    EVENT_RE,
    FOREACH_RE,
    MACRO_RE,
    MAX_LOOP_ITEMS,
    MAX_LOOPS,
    NODE_COMMANDS,
    PICTURE_RE,
)
from ._tikz_syntax import _balanced, _dimension, _measure, _options, _split

if TYPE_CHECKING:
    from ._tikz_syntax import Pair, Point

__all__: list[str] = []


@dataclass
class _Frame:
    """The picture's coordinate system: unit vectors and scale, mapped to y-down user units."""

    x_unit: float = DEFAULT_UNIT
    y_unit: float = DEFAULT_UNIT
    x_scale: float = 1.0
    y_scale: float = 1.0
    matrix: Matrix = IDENTITY

    def vector(self, text: str) -> Point:
        """SVG offset of a coordinate ``x,y`` or ``angle:radius``, through the scope transform."""
        x, y = self._raw(text)
        m = self.matrix
        return m.a * x + m.c * y, m.b * x + m.d * y

    def absolute(self, text: str) -> Point:
        """SVG position of a coordinate, through the scope transform."""
        x, y = self.vector(text)
        return x + self.matrix.e, y + self.matrix.f

    def scoped(self, pairs: list[Pair]) -> _Frame:
        """The frame inside a scope with these options: ``shift``, ``xshift``, ``yshift``, ``scale``, ``rotate``."""
        matrix = self.matrix
        for key, value in pairs:
            try:
                step = self._step(key, value or "")
            except ValueError:
                continue
            matrix = matrix if step is None else matrix @ step
        return replace(self, matrix=matrix)

    def _step(self, key: str, value: str) -> Matrix | None:
        """The transform one scope option adds, None for other options."""
        if key == "shift":
            return Matrix.translate(*self._raw(_balanced(value, 0)[0] if value.startswith("(") else value))
        if key in ("xshift", "yshift"):
            offset = _measure(value)
            return Matrix.translate(offset, 0.0) if key == "xshift" else Matrix.translate(0.0, -offset)
        if key == "rotate":
            return Matrix.rotate(-float(value))
        if key in ("scale", "xscale", "yscale"):
            factor = float(value)
            return Matrix.scale(1.0 if key == "yscale" else factor, 1.0 if key == "xscale" else factor)
        return None

    def _raw(self, text: str) -> Point:
        """Offset of a coordinate in the picture's axes."""
        if ":" in text and "," not in text:
            angle, radius = text.split(":", 1)
            r, unit = _dimension(radius)
            a = math.radians(float(angle))
            return self._map(r * math.cos(a), r * math.sin(a), unit, unit)
        parts = _split(text)
        if len(parts) != 2:
            raise ValueError(f"unsupported TikZ coordinate: ({text})")
        (x, x_unit), (y, y_unit) = _dimension(parts[0]), _dimension(parts[1])
        return self._map(x, y, x_unit, y_unit)

    def radii(self, x: str, y: str) -> Point:
        """Ellipse radii in SVG units."""
        (rx, x_unit), (ry, y_unit) = _dimension(x), _dimension(y)
        m = self.matrix
        return (abs(rx * self.x_scale * (1.0 if x_unit else self.x_unit)) * math.hypot(m.a, m.b),
                abs(ry * self.y_scale * (1.0 if y_unit else self.y_unit)) * math.hypot(m.c, m.d))

    def _map(self, x: float, y: float, x_unit: bool, y_unit: bool) -> Point:
        """Scale a coordinate and flip y; unitless components use the unit vectors."""
        return (x * self.x_scale * (1.0 if x_unit else self.x_unit),
                -y * self.y_scale * (1.0 if y_unit else self.y_unit))


def _picture_options(text: str) -> str:
    """The option list of the first ``tikzpicture`` environment, empty when it has none."""
    match = PICTURE_RE.search(text)
    if match is None:
        return ""
    start = match.end() + len(text[match.end():]) - len(text[match.end():].lstrip())
    if start >= len(text) or text[start] != "[":
        return ""
    return _balanced(text, start)[0]


def _frame(options: str) -> _Frame:
    """The frame set by a ``tikzpicture``'s ``x``, ``y`` and scale options."""
    frame = _Frame()
    for key, value in _options(options):
        try:
            if key in ("x", "y") and value is not None:
                setattr(frame, f"{key}_unit", _measure(value))
            elif key in ("scale", "xscale", "yscale") and value is not None:
                for axis in ("x", "y") if key == "scale" else (key[0],):
                    setattr(frame, f"{axis}_scale", getattr(frame, f"{axis}_scale") * float(value))
        except ValueError:
            continue
    return frame


@dataclass(frozen=True)
class _Scope:
    """The coordinate frame and the options in force inside a scope."""

    frame: _Frame
    pairs: list[Pair]

    def child(self, pairs: list[Pair]) -> _Scope:
        """The scope opened inside this one with *pairs*."""
        return _Scope(self.frame.scoped(pairs), self.pairs + pairs)


def _statement(text: str, start: int) -> tuple[str, int]:
    """The path text from *start* up to the ``;`` outside brackets."""
    depth = 0
    for i in range(start, len(text)):
        char = text[i]
        depth += (char in "{[(") - (char in "}])")
        if char == ";" and depth <= 0:
            return text[start:i], i + 1
    return text[start:], len(text)


def _events(text: str) -> list[tuple[str, str, str, str]]:
    """``(kind, command, options, path)`` in order: ``begin``/``end`` of scopes and ``cmd`` for path commands.

    A ``\\node`` or ``\\coordinate`` is read as ``\\path node ...``: its options stay in its path.
    """
    out, pos = [], 0
    while (match := EVENT_RE.search(text, pos)) is not None:
        pos = match.end() + len(text[match.end():]) - len(text[match.end():].lstrip())
        command, options = match.group(2) or "", ""
        if match.group(1) == "end":
            out.append(("end", "", "", ""))
            continue
        if command in NODE_COMMANDS:
            body, pos = _statement(text, match.end())
            out.append(("cmd", command, "", command + body))
            continue
        if pos < len(text) and text[pos] == "[":
            options, pos = _balanced(text, pos)
        if match.group(1):
            out.append(("begin", "", options, ""))
            continue
        body, pos = _statement(text, pos)
        out.append(("cmd", command, options, body))
    return out


def _loop_items(text: str) -> list[str]:
    """The values of a ``\\foreach`` list, with ``a,b,...,z`` expanded as an arithmetic progression."""
    parts = _split(text)
    if "..." not in parts:
        return parts
    k = parts.index("...")
    head, stop = [float(part) for part in parts[:k]], float(parts[k + 1])
    step = head[-1] - head[-2] if len(head) > 1 else math.copysign(1.0, stop - head[0])
    count = math.floor((stop - head[0]) / step + 1e-9) + 1
    if count > MAX_LOOP_ITEMS:
        raise ValueError("\\foreach list too long")
    return [f"{head[0] + j * step:g}" for j in range(count)]


def _unrolled(text: str, match: re.Match[str]) -> tuple[str, int]:
    """The repeated body of the ``\\foreach`` at *match*, and the index where the loop ends."""
    names = MACRO_RE.findall(match.group(1))
    if text[match.end()] != "{":
        raise ValueError("\\foreach list must be in braces")
    items, pos = _balanced(text, match.end())
    pos += len(text[pos:]) - len(text[pos:].lstrip())
    if text[pos] == "{":
        body, end = _balanced(text, pos)
    else:
        body, end = _statement(text, pos)
        body += ";"
    copies = []
    for item in _loop_items(items):
        values = dict(zip(names, item.split("/") if len(names) > 1 else [item], strict=False))
        copies.append(MACRO_RE.sub(lambda m, v=values: v.get(m.group(), m.group()), body))
    return "\n".join(copies), end


def _unroll(text: str) -> str:
    """*text* with each ``\\foreach`` replaced by its body once per value, the variable substituted."""
    for _ in range(MAX_LOOPS):
        match = FOREACH_RE.search(text)
        if match is None:
            break
        try:
            body, end = _unrolled(text, match)
        except (ValueError, IndexError):
            body, end = "", match.end()
        text = text[:match.start()] + body + text[end:]
    return text


def _bounds(ops: list) -> tuple[float, float, float, float] | None:
    """``(min_x, min_y, width, height)`` of the points in *ops*, None when empty or flat."""
    xs = [v for _, args in ops for v in args[0::2]]
    ys = [v for _, args in ops for v in args[1::2]]
    if not xs or max(xs) <= min(xs) or max(ys) <= min(ys):
        return None
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
