from dataclasses import dataclass
from ...document import Document

__all__ = ["Equation", "split_equations"]

@dataclass(frozen=True)
class Equation:
    source: str
    x: float
    y: float
    width: float
    height: float
    size: float

    def __init__(
        self,
        source: str,
        x: float,
        y: float,
        width: float,
        height: float,
        size: float,
    ) -> None: ...

def split_equations(document: Document) -> tuple[Document, list[Equation]]: ...
