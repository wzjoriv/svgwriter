from ..elements.base import Element

__all__ = ["matches_compound", "specificity"]

def specificity(selector: str) -> tuple[int, int, int]: ...

def matches_compound(element: Element, compound: str) -> bool: ...
