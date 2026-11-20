from typing import Any
from ..._internal._typing import Self

__all__ = ["ColorMatrixShortcuts"]

class ColorMatrixShortcuts:
    @classmethod
    def saturate(cls, amount: float, **kwargs: Any) -> Self: ...
    @classmethod
    def hue_rotate(cls, degrees: float, **kwargs: Any) -> Self: ...
    @classmethod
    def luminance_to_alpha(cls, **kwargs: Any) -> Self: ...
    @classmethod
    def grayscale(cls, **kwargs: Any) -> Self: ...
