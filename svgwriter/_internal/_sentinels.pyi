from enum import Enum
from typing import Final, Literal

__all__ = ["MISSING", "MissingType"]

class MissingType(Enum):
    MISSING = 1

    def __repr__(self) -> str: ...
    def __bool__(self) -> Literal[False]: ...

MISSING: Final = ...
