import numpy as np
from collections.abc import Callable
from typing import Final
from numpy import ndarray

__all__ = ["ENCODERS", "encode_bmp"]

def encode_bmp(rgba: ndarray) -> bytes: ...

ENCODERS: Final[dict[str, Callable[[np.ndarray], bytes]]]
