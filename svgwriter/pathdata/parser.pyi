from collections.abc import Iterator
from .commands import PathCommand

__all__ = ["PathSyntaxError", "iter_commands", "parse_path"]

class PathSyntaxError(ValueError):
    position: int

    def __init__(self, message: str, position: int) -> None: ...

def iter_commands(text: str) -> Iterator[PathCommand]: ...

def parse_path(text: str) -> list[PathCommand]: ...
