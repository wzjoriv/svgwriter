from typing import Any
from ...elements.core._element import Element
from ._pdf_painter import _Painter

__all__ = ["fill_with_pattern", "paint_shading", "pattern_paint"]

def paint_shading(
    painter: _Painter,
    operands: list[Any],
    resources: dict[str, Any],
) -> None: ...

def pattern_paint(painter: _Painter, pattern: Any) -> Element | None: ...

def fill_with_pattern(
    painter: _Painter,
    ops: list[Any],
    evenodd: bool,
    stroke: bool,
) -> bool: ...
