from enum import IntEnum
from .._internal._typing import AnyPath
from ..elements.base import Element

__all__ = ["SVGParseError", "Strictness", "parse", "parse_file"]

class Strictness(IntEnum):
    LENIENT = 0
    WARN = 1
    STRICT = 2

class SVGParseError(ValueError):
    ...

def parse(
    source: str | bytes,
    *,
    strictness: Strictness = Strictness.LENIENT,
) -> Element: ...

def parse_file(
    path: AnyPath,
    *,
    strictness: Strictness = Strictness.LENIENT,
) -> Element: ...
