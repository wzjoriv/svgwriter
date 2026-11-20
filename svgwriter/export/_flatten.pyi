from dataclasses import dataclass
from typing import Any
from ..color.color import Color
from ..document import Document
from ..pathdata.data import PathData
from ._paints import Shading

__all__ = ["Item", "Scene", "flatten", "to_cubic"]

@dataclass
class Item:
    data: PathData
    fill: Color | None
    fill_opacity: float
    evenodd: bool
    stroke: Color | None
    stroke_opacity: float
    stroke_width: float
    linecap: str
    linejoin: str
    miter_limit: float
    dashes: tuple[float, ...]
    shading: Shading | None = None

    def __init__(
        self,
        data: PathData,
        fill: Color | None,
        fill_opacity: float,
        evenodd: bool,
        stroke: Color | None,
        stroke_opacity: float,
        stroke_width: float,
        linecap: str,
        linejoin: str,
        miter_limit: float,
        dashes: tuple[float, ...],
        shading: Shading | None = None,
    ) -> None: ...

@dataclass
class Scene:
    width: float
    height: float
    items: list[Item]
    skipped: list[str]
    texts: list[Any] = ...

    def __init__(
        self,
        width: float,
        height: float,
        items: list[Item],
        skipped: list[str],
        texts: list[Any] = ...,
    ) -> None: ...

def to_cubic(data: PathData) -> list[tuple[str, tuple[float, ...]]]: ...

def flatten(
    document: Document,
    *,
    handled: frozenset[str] = ...,
    text: bool = False,
) -> Scene: ...
