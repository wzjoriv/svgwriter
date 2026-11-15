"""Paint servers: gradients, stops and patterns."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, ClassVar, TypeAlias

from .._internal._typing import Opacity, Self, SpreadMethod, Units
from ..attributes.length import LengthLike
from ..color.color import Color
from ..path.data import BBox
from ._mixins import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    PresentationAttributes,
    Transformable,
    XLinkAttributes,
)
from ._viewport import FitToViewBox, Positioned, positioned_bbox, user_units
from .base import Category, Child
from .container import Container, GraphicsContainer

__all__ = ["Gradient", "LinearGradient", "Pattern", "RadialGradient", "Stop", "StopSpec"]

StopSpec: TypeAlias = tuple[float, Color | str] | tuple[float, Color | str, float]


class Stop(PresentationAttributes, CoreAttributes, tag="stop", category=Category.GRADIENT):
    """``<stop>``: one color stop of a gradient."""

    def __init__(
        self,
        offset: float | str = 0,
        stop_color: Color | str | None = None,
        stop_opacity: Opacity | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(offset=offset, stop_color=stop_color, stop_opacity=stop_opacity)


class Gradient(
    Transformable,
    XLinkAttributes,
    ExternalResourcesAttribute,
    PresentationAttributes,
    CoreAttributes,
    Container[Stop],
    category=Category.GRADIENT,
):
    """Shared base of linear and radial gradients."""

    def __init__(
        self,
        *stops: Stop,
        gradient_units: Units | None = None,
        spread_method: SpreadMethod | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*stops, **kwargs)
        self.update(gradient_units=gradient_units, spread_method=spread_method)

    transform_attribute: ClassVar[str] = "gradientTransform"

    def _units_bbox(self, units_attribute: str) -> BBox | None:
        if str(self.get(units_attribute, "objectBoundingBox")) == "objectBoundingBox":
            return BBox(0.0, 0.0, 1.0, 1.0)
        return None

    def add_stop(self, offset: float, color: Color | str, opacity: Opacity | None = None, **kwargs: Any) -> Stop:
        return self.add(Stop(offset, color, opacity, **kwargs))

    @classmethod
    def from_colors(cls, colors: Sequence[Color | str], **kwargs: Any) -> Self:
        """Evenly spaced stops."""
        gradient = cls(**kwargs)
        last = max(len(colors) - 1, 1)
        for index, color in enumerate(colors):
            gradient.add_stop(index / last, color)
        return gradient

    @classmethod
    def from_stops(cls, stops: Iterable[StopSpec], **kwargs: Any) -> Self:
        gradient = cls(**kwargs)
        for spec in stops:
            gradient.add_stop(*spec)
        return gradient


class LinearGradient(Gradient, tag="linearGradient"):
    """``<linearGradient>``.

    Parameters
    ----------
    *stops : Stop
        Color stops.
    x1, y1, x2, y2 : length, optional
        The gradient vector.
    **kwargs
        ``gradient_units``, ``spread_method``, ``transform``, ``href`` and
        presentation/core attributes.
    """

    def __init__(
        self,
        *stops: Stop,
        x1: LengthLike | None = None,
        y1: LengthLike | None = None,
        x2: LengthLike | None = None,
        y2: LengthLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*stops, **kwargs)
        self.update(x1=x1, y1=y1, x2=x2, y2=y2)

    def local_bbox(self) -> BBox | None:
        box = self._units_bbox("gradientUnits")
        if box is not None:
            return box
        x1, y1, x2, y2 = (user_units(self.get(n, d)) for n, d in (("x1", 0), ("y1", 0), ("x2", "100%"), ("y2", 0)))
        return BBox.from_points([(x1, y1), (x2, y2)])

    @classmethod
    def horizontal(cls, *colors: Color | str, **kwargs: Any) -> Self:
        return cls.from_colors(colors, x1=0, y1=0, x2=1, y2=0, **kwargs)

    @classmethod
    def vertical(cls, *colors: Color | str, **kwargs: Any) -> Self:
        return cls.from_colors(colors, x1=0, y1=0, x2=0, y2=1, **kwargs)


class RadialGradient(Gradient, tag="radialGradient"):
    """``<radialGradient>``."""

    def __init__(
        self,
        *stops: Stop,
        cx: LengthLike | None = None,
        cy: LengthLike | None = None,
        r: LengthLike | None = None,
        fx: LengthLike | None = None,
        fy: LengthLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*stops, **kwargs)
        self.update(cx=cx, cy=cy, r=r, fx=fx, fy=fy)

    def local_bbox(self) -> BBox | None:
        box = self._units_bbox("gradientUnits")
        if box is not None:
            return box
        cx, cy, r = (user_units(self.get(n, 0)) for n in ("cx", "cy", "r"))
        return BBox(cx - r, cy - r, 2 * r, 2 * r)


class Pattern(
    Transformable,
    Positioned,
    FitToViewBox,
    XLinkAttributes,
    ExternalResourcesAttribute,
    PresentationAttributes,
    ConditionalAttributes,
    CoreAttributes,
    GraphicsContainer,
    tag="pattern",
    category=Category.PAINT_SERVER,
):
    """``<pattern>``: a tile of graphics used as paint."""

    def __init__(
        self,
        *children: Child,
        pattern_units: Units | None = None,
        pattern_content_units: Units | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        self.update(pattern_units=pattern_units, pattern_content_units=pattern_content_units)

    transform_attribute: ClassVar[str] = "patternTransform"

    def local_bbox(self) -> BBox | None:
        return positioned_bbox(self)
