from dataclasses import dataclass
from typing import Final
from ..elements.core._element import Element

__all__ = ["INHERITED", "Rule", "computed", "parse_css", "resolve_styles", "rules_of"]

INHERITED: Final = ...

@dataclass(frozen=True)
class Rule:
    selector: str
    specificity: tuple[int, int, int]
    order: int
    declarations: tuple[tuple[str, str, bool], ...]

    def __init__(
        self,
        selector: str,
        specificity: tuple[int, int, int],
        order: int,
        declarations: tuple[tuple[str, str, bool], ...],
    ) -> None: ...

def parse_css(text: str, start: int = 0) -> list[Rule]: ...

def rules_of(root: Element) -> list[Rule]: ...

def computed(
    element: Element,
    name: str,
    default: object = None,
    rules: list[Rule] | None = None,
) -> object: ...

def resolve_styles(root: Element) -> None: ...
