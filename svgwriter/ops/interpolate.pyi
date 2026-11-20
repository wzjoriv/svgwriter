from typing import TypeVar

__all__ = ["interpolate"]

T = TypeVar('T')

def interpolate(
    a: T,
    b: T,
    t: float,
) -> T: ...
