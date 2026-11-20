from dataclasses import dataclass
from ..color.color import Color
from ..document import Document
from ..pathdata.data import PathData
from ..transform.matrix import Matrix

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

    def __init__(
        self,
        width: float,
        height: float,
        items: list[Item],
        skipped: list[str],
    ) -> None: ...

def to_cubic(data: PathData) -> list[tuple[str, tuple[float, ...]]]: ...

@dataclass
class Shading:
    kind: str
    coords: tuple[float, ...]
    stops: list[tuple[float, Color]]
    matrix: Matrix

    def __init__(
        self,
        kind: str,
        coords: tuple[float, ...],
        stops: list[tuple[float, Color]],
        matrix: Matrix,
    ) -> None: ...

def flatten(
    document: Document,
    *,
    handled: frozenset[str] = ...,
) -> Scene: ...
