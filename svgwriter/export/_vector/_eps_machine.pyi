from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final
from ...transform.matrix import Matrix
from ._eps_syntax import _Font
from ._reading import RGB, Outline

__all__ = ["OPERATORS"]

@dataclass
class _State:
    ctm: Matrix
    color: RGB = (0.0, 0.0, 0.0)
    line_width: float = 1.0
    cap: int = 0
    join: int = 0
    miter: float = 10.0
    dashes: tuple[float, ...] = ()
    font: _Font | None = None
    clip: list[tuple[str, tuple[float, ...]]] | None = None

    def __init__(
        self,
        ctm: Matrix,
        color: RGB = (0.0, 0.0, 0.0),
        line_width: float = 1.0,
        cap: int = 0,
        join: int = 0,
        miter: float = 10.0,
        dashes: tuple[float, ...] = (),
        font: _Font | None = None,
        clip: list[tuple[str, tuple[float, ...]]] | None = None,
    ) -> None: ...

class _Machine:
    stack: list[Any]
    dicts: list[dict[str, Any]]
    state: Any
    saved: list[tuple[_State, Outline]]
    outline: Outline
    shapes: list[Any]
    file_data: Any
    steps: int
    done: bool

    def __init__(self, ctm: Matrix) -> None: ...
    def execute(self, program: list[Any], depth: int = 0) -> None: ...
    def call(self, name: str, depth: int) -> None: ...
    def lookup(self, name: str) -> tuple[bool, Any]: ...
    def pop(self, count: int = 1, kind: type | tuple[type, ...] = float) -> list[Any]: ...
    def paint(
        self,
        fill: bool,
        evenodd: bool = False,
        ops: list | None = None,
    ) -> None: ...
    def relative(self, *offsets: float) -> list[float]: ...
    def transform(self, matrix: Matrix) -> None: ...

OPERATORS: Final[dict[str, Callable[[_Machine, int], None]]]
