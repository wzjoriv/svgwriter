from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias
from ..attributes.reference import FuncIRI
from ..elements.core._element import Element
from .color import Color

__all__ = ["Paint", "PaintKeyword", "PaintRef", "PaintValue", "parse_paint"]

class PaintKeyword(str, Enum):
    NONE = 'none'
    CURRENT_COLOR = 'currentColor'
    INHERIT = 'inherit'

    def __str__(self) -> str: ...

@dataclass(frozen=True)
class PaintRef:
    iri: FuncIRI
    fallback: Color | PaintKeyword | None = None

    def __init__(self, iri: FuncIRI, fallback: Color | PaintKeyword | None = None) -> None: ...
    def svg_value(self, precision: int = 4) -> str: ...
    def __str__(self) -> str: ...

Paint: TypeAlias = Color | PaintKeyword | PaintRef
PaintValue: TypeAlias = Paint | str | Element | Sequence[float] | None

def parse_paint(text: str) -> Paint: ...
