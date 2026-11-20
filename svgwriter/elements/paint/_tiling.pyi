from typing import Any
from ...pathdata.data import BBox
from ..structure import Group, Image
from ._servers import Pattern

__all__ = ["PatternTiling"]

class PatternTiling:
    def tile(self, target: BBox | None = None) -> BBox: ...
    def to_image(
        self,
        *,
        scale: float = 1.0,
        target: BBox | None = None,
    ) -> Image: ...
    @classmethod
    def from_image(cls, image: Image, **kwargs: Any) -> Pattern: ...
    def tiles(
        self,
        area: BBox,
        *,
        target: BBox | None = None,
    ) -> Group: ...
