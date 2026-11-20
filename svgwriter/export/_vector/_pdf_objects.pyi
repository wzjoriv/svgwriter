from dataclasses import dataclass
from typing import Any

__all__ = ["Name", "Operator", "Ref", "Stream"]

class Name(str):
    ...

class Operator(str):
    ...

@dataclass(frozen=True)
class Ref:
    number: int

    def __init__(self, number: int) -> None: ...

@dataclass
class Stream:
    info: dict[str, Any]
    raw: bytes

    def __init__(self, info: dict[str, Any], raw: bytes) -> None: ...
