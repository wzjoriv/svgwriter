from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from ..pathdata.data import PathData
from .text import Anchor, FontWeight

__all__ = ["GlyphBox", "layout_glyphs"]

@dataclass
class GlyphBox:
    char: str
    outline: PathData
    x: float
    y: float
    angle: float
    advance: float
    source: Any = None

    def __init__(
        self,
        char: str,
        outline: PathData,
        x: float,
        y: float,
        angle: float,
        advance: float,
        source: Any = None,
    ) -> None: ...
    def placed(self) -> PathData: ...

def layout_glyphs(
    text: str,
    font_family: str = 'sans-serif',
    size: float = 16.0,
    *,
    x: Sequence[float] = (0.0,),
    y: Sequence[float] = (0.0,),
    dx: Sequence[float] = (),
    dy: Sequence[float] = (),
    rotate: Sequence[float] = (),
    anchor: Anchor = 'start',
    weight: FontWeight = 'normal',
    italic: bool = False,
) -> list[GlyphBox]: ...
