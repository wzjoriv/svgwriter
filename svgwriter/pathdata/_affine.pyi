from collections.abc import Iterable, Iterator
from ..transform.matrix import Matrix
from .commands import ArcTo, PathCommand

__all__ = ["transform_arc", "transform_commands"]

def transform_arc(arc: ArcTo, matrix: Matrix) -> ArcTo: ...

def transform_commands(commands: Iterable[PathCommand], matrix: Matrix) -> Iterator[PathCommand]: ...
