from dataclasses import dataclass
from ...document import Document
from ...elements.core import Element
from ...pathdata.data import BBox

__all__ = ["Equation", "page_box", "split_equations"]

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

def page_box(document: Document, element: Element) -> tuple[BBox | None, float]: ...

def split_equations(document: Document) -> tuple[Document, list[Equation]]: ...
