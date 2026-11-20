from collections.abc import Sequence
from numpy import ndarray

__all__ = ["encode_apng", "encode_webp_animation"]

def encode_apng(
    frames: Sequence[ndarray],
    fps: float,
    *,
    loop: int = 0,
) -> bytes: ...

def encode_webp_animation(
    frames: Sequence[ndarray],
    fps: float,
    *,
    loop: int = 0,
) -> bytes: ...
