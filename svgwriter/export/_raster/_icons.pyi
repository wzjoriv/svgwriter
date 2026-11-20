from collections.abc import Iterable
from ...document import Document
from ._constants import ICNS_SIZES as ICNS_SIZES, ICO_SIZES as ICO_SIZES

__all__ = ["ICNS_SIZES", "ICO_SIZES", "read_icon", "to_icns", "to_ico"]

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
