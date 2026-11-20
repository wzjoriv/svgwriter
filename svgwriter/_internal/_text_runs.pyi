from dataclasses import dataclass
from ..color.color import Color
from ..document import Document
from ..transform.matrix import Matrix

__all__ = ["TextRun", "text_runs"]

@dataclass
class TextRun:
    text: str
    matrix: Matrix
    size: float
    family: str
    bold: bool
    italic: bool
    fill: Color | None
    opacity: float
    width: float

    def __init__(
        self,
        text: str,
        matrix: Matrix,
        size: float,
        family: str,
        bold: bool,
        italic: bool,
        fill: Color | None,
        opacity: float,
        width: float,
    ) -> None: ...

def text_runs(document: Document) -> list[TextRun]: ...
