import numpy as np
from collections.abc import Mapping
from typing import Any, TypeVar
from ...color.color import ColorLike
from ...pathdata.data import BBox
from ...transform.transform import TransformLike
from ..core._element import AttrValue, Element
from ..paint._clip import ClipPath
from ..shapes import Path
from ..structure import Group, Image
from ._transformable import PointLike, Transformable

__all__ = ["Convertible"]

E = TypeVar('E', bound='Convertible')

class Convertible(Transformable):
    def to_path(self, **kwargs: Any) -> Path: ...
    def to_group(
        self,
        *,
        t: TransformLike | None = None,
        transform: TransformLike | None = None,
        anchor: PointLike | None = None,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **kwargs: Any,
    ) -> Group: ...
    def to_image(
        self,
        *,
        scale: float = 1.0,
        padding: float = 0.0,
        background: ColorLike | None = None,
    ) -> Image: ...
    def clip(self: E, *shapes: Element, units: str | None = None) -> E: ...
    def unclip(self: E) -> E: ...
    @property
    def clip_region(self) -> ClipPath | None: ...
    def render_bounds(self) -> BBox | None: ...
    def rasterize(
        self,
        *,
        scale: float = 1.0,
        size: tuple[int, int] | int | None = None,
        padding: float = 0.0,
        background: ColorLike | None = None,
    ) -> np.ndarray: ...
