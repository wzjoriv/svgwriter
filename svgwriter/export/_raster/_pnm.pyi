from collections.abc import Sequence
from numpy import ndarray

__all__ = ["decode_pnm", "encode_pnm", "is_pnm"]

def encode_pnm(
    rgba: ndarray,
    *,
    gray: bool | None = None,
    background: Sequence[int] = (255, 255, 255),
) -> bytes: ...

def is_pnm(data: bytes) -> bool: ...

def decode_pnm(data: bytes) -> ndarray: ...
