from dataclasses import dataclass
from ...attributes.cascade import Rule
from ...ops.text import GlyphBox
from ..core import Element

__all__ = ["Char", "collect", "layout", "number_list"]

@dataclass
class Char:
    char: str
    chain: tuple[Element, ...]
    child: int
    offset: int
    local: dict[int, int]

    def __init__(
        self,
        char: str,
        chain: tuple[Element, ...],
        child: int,
        offset: int,
        local: dict[int, int],
    ) -> None: ...

def number_list(value: object, reference: float = 0.0) -> list[float]: ...

def collect(text: Element) -> list[Char]: ...

def layout(text: Element, rules: list[Rule] | None = None) -> list[GlyphBox]: ...
