from typing import TypeAlias

__all__ = ["Pair", "Point"]

Point: TypeAlias = tuple[float, float]
Pair: TypeAlias = tuple[str, str | None]
