from typing import Any

__all__ = ["MatrixText"]

class MatrixText:
    def svg_value(
        self,
        precision: int = 4,
        *,
        pivot: tuple[float, float] | None = None,
        box: Any = None,
    ) -> str: ...
