from typing import Any
from .text import FontWeight

__all__ = ["font_for", "registered_face", "registered_typefaces", "resolve_font", "weight_value"]

def weight_value(value: FontWeight) -> int: ...

registered_typefaces: dict[str, list[Any]]

def registered_face(
    family: str,
    weight: int,
    slant: Any,
) -> Any: ...

def resolve_font(
    font_family: str,
    size: float,
    weight: FontWeight,
    italic: bool,
) -> Any: ...

def font_for(
    char: str,
    font_family: str,
    size: float,
    weight: FontWeight = 'normal',
    italic: bool = False,
    language: str | None = None,
) -> Any: ...
