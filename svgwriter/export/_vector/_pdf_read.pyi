from dataclasses import dataclass
from typing import Any
from ...document import Document
from ...transform.matrix import Matrix
from ._reading import RGB, Op, Outline

__all__ = ["read_pdf"]

@dataclass
class _State:
    ctm: Matrix
    fill: RGB = (0.0, 0.0, 0.0)
    stroke: RGB = (0.0, 0.0, 0.0)
    fill_alpha: float = 1.0
    stroke_alpha: float = 1.0
    group_alpha: float = 1.0
    line_width: float = 1.0
    cap: int = 0
    join: int = 0
    miter: float = 4.0
    dashes: tuple[float, ...] = ()
    clip: list[Op] | None = None

    def __init__(
        self,
        ctm: Matrix,
        fill: RGB = (0.0, 0.0, 0.0),
        stroke: RGB = (0.0, 0.0, 0.0),
        fill_alpha: float = 1.0,
        stroke_alpha: float = 1.0,
        group_alpha: float = 1.0,
        line_width: float = 1.0,
        cap: int = 0,
        join: int = 0,
        miter: float = 4.0,
        dashes: tuple[float, ...] = (),
        clip: list[Op] | None = None,
    ) -> None: ...

class _Painter:
    objects: dict[int, Any]
    state: Any
    saved: list[_State]
    outline: Outline
    shapes: list[Any]
    depth: int
    pending_clip: bool | None
    text_matrix: Matrix
    line_matrix: Matrix
    leading: float

    def __init__(self, objects: dict[int, Any], ctm: Matrix) -> None: ...
    def run(self, content: bytes, resources: dict[str, Any]) -> None: ...
    def resource(
        self,
        resources: dict[str, Any],
        category: str,
        name: Any,
    ) -> Any: ...
    def take(self) -> list[Op]: ...
    def paint(
        self,
        fill: bool,
        stroke: bool,
        evenodd: bool,
    ) -> None: ...
    def form(self, xobject: Any, resources: dict[str, Any]) -> None: ...

def read_pdf(
    data: bytes,
    *,
    page: int = 0,
) -> Document: ...
