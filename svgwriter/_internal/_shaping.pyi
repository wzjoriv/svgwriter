from dataclasses import dataclass
from typing import Any
from ..pathdata import PathData

__all__ = ["ColorGlyphs", "harfbuzz", "hb_font", "needs_shaping", "shape_run"]

@dataclass(frozen=True)
class ColorGlyphs:
    text: str
    font: Any
    glyphs: tuple[int, ...]
    offsets: tuple[tuple[float, float], ...]

    def __init__(
        self,
        text: str,
        font: Any,
        glyphs: tuple[int, ...],
        offsets: tuple[tuple[float, float], ...],
    ) -> None: ...

def harfbuzz() -> Any: ...

def hb_font(typeface: Any) -> Any: ...

def needs_shaping(text: str) -> bool: ...

def shape_run(text: str, font: Any) -> list[tuple[PathData, float, ColorGlyphs | None]]: ...
