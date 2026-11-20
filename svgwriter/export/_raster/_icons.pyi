from collections.abc import Iterable
from typing import Final
from ...document import Document

__all__ = ["ICNS_SIZES", "ICO_SIZES", "read_icon", "to_icns", "to_ico"]

ICO_SIZES: Final = ...
ICNS_SIZES: Final = ...

def to_ico(
    document: Document,
    *,
    sizes: Iterable[int] = (16, 24, 32, 48, 64, 128, 256),
    padding: float = 0.0,
) -> bytes: ...

def to_icns(
    document: Document,
    *,
    sizes: Iterable[int] = (16, 32, 64, 128, 256, 512, 1024),
    padding: float = 0.0,
) -> bytes: ...

def read_icon(data: bytes) -> Document: ...
