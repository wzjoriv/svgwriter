from dataclasses import dataclass
from ...transform.matrix import Matrix

__all__ = ["Inline", "Literal", "Mark", "Name", "Procedure"]

class Name(str):
    ...

class Literal(str):
    ...

class Procedure(list):
    ...

class Mark:
    ...

class Inline(bytes):
    ...

class _File:
    ...

@dataclass
class _Font:
    name: str
    matrix: Matrix

    def __init__(self, name: str, matrix: Matrix) -> None: ...

class _Underflow(Exception):
    ...
