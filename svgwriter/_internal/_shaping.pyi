from typing import Any
from ..ops.text import FontWeight
from ..pathdata import PathData

__all__ = ["harfbuzz", "hb_font", "needs_shaping", "shape_run"]

def harfbuzz() -> Any: ...

def hb_font(typeface: Any) -> Any: ...

def needs_shaping(text: str) -> bool: ...

def shape_run(
    text: str,
    font_family: str,
    size: float,
    weight: FontWeight = 'normal',
    italic: bool = False,
    language: str | None = None,
) -> list[tuple[PathData, float]]: ...
