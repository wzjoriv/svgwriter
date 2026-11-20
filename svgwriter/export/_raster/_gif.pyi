from collections.abc import Sequence
from numpy import ndarray

__all__ = ["encode_gif", "encode_gif_animation"]

def encode_gif(rgba: ndarray) -> bytes: ...

def encode_gif_animation(
    frames: Sequence[ndarray],
    fps: float,
    *,
    loop: int = 0,
) -> bytes: ...
