import numpy as np
from collections.abc import Callable, Sequence
from typing import Final
from numpy import ndarray

__all__ = ["ENCODERS", "decode_pnm", "encode_bmp", "encode_gif", "encode_pnm", "is_pnm", "to_uint8"]

def to_uint8(array: object) -> ndarray: ...

def encode_bmp(rgba: ndarray) -> bytes: ...

def encode_pnm(
    rgba: ndarray,
    *,
    gray: bool | None = None,
    background: Sequence[int] = (255, 255, 255),
) -> bytes: ...

def encode_gif(rgba: ndarray) -> bytes: ...

ENCODERS: Final[dict[str, Callable[[np.ndarray], bytes]]]

def is_pnm(data: bytes) -> bool: ...

def decode_pnm(data: bytes) -> ndarray: ...
