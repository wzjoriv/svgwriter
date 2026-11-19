"""
Paint servers: gradients, stops and patterns.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, ClassVar, TypeAlias

from .._internal._typing import Opacity, Self, SpreadMethod, Units
from ..attributes.length import LengthLike
from ..color.color import Color
from ..pathdata.data import BBox
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
    """``<stop>``: one color stop of a gradient.

    Parameters
    ----------
    offset : float or str, optional
        Position along the gradient vector, 0 to 1 or a percentage. Defaults to 0.
    stop_color : Color or str, optional
        The color at the offset.
    stop_opacity : float, optional
        The opacity at the offset.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Gradient.add_stop : Create and append a stop in one call.

    Examples
    --------
    >>> str(Stop(0.5, "red", 0.5))
    '<stop offset="0.5" stop-color="red" stop-opacity="0.5"/>'
    """

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
    """Shared base of linear and radial gradients.

    Holds the color stops and the attributes common to both kinds.

    Parameters
    ----------
    *stops : Stop
        Color stops.
    gradient_units : {"objectBoundingBox", "userSpaceOnUse"}, optional
        Coordinate system of the gradient vector. Defaults to None.
    spread_method : {"pad", "reflect", "repeat"}, optional
        What happens beyond the ends of the vector. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    LinearGradient : Gradient along a line.
    RadialGradient : Gradient around a center.

    Examples
    --------
    >>> import svgwriter as svg
    >>> grad = svg.LinearGradient(svg.Stop(0, "red"), svg.Stop(1, "blue"))
    >>> isinstance(grad, svg.Gradient), len(grad)
    (True, 2)
    """

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
        """Append a color stop and return it.

        Parameters
        ----------
        offset : float
            Position along the gradient vector, 0 to 1.
        color : Color or str
            The stop color.
        opacity : float, optional
            The stop opacity. Defaults to None.
        **kwargs
            Further attributes of the :class:`Stop`.

        Returns
        -------
        Stop
            The new stop, already a child of the gradient.

        Examples
        --------
        >>> g = LinearGradient()
        >>> _ = g.add_stop(0, "red")
        >>> str(g)
        '<linearGradient><stop offset="0" stop-color="red"/></linearGradient>'
        """
        return self.add(Stop(offset, color, opacity, **kwargs))

    @classmethod
    def from_colors(cls, colors: Sequence[Color | str], **kwargs: Any) -> Self:
        """Create a gradient with evenly spaced stops.

        Parameters
        ----------
        colors : sequence of Color or str
            One color per stop, the first at offset 0 and the last at 1.
        **kwargs
            Attributes of the gradient.

        Returns
        -------
        Gradient
            A new gradient of the calling class.

        Examples
        --------
        >>> g = LinearGradient.from_colors(["red", "blue"])
        >>> [s.get("offset") for s in g]
        [0.0, 1.0]
        """
        gradient = cls(**kwargs)
        last = max(len(colors) - 1, 1)
        for index, color in enumerate(colors):
            gradient.add_stop(index / last, color)
        return gradient

    @classmethod
    def from_stops(cls, stops: Iterable[StopSpec], **kwargs: Any) -> Self:
        """Create a gradient from ``(offset, color)`` or ``(offset, color, opacity)`` tuples.

        Parameters
        ----------
        stops : iterable of tuple
            Stop specifications.
        **kwargs
            Attributes of the gradient.

        Returns
        -------
        Gradient
            A new gradient of the calling class.

        Examples
        --------
        >>> g = LinearGradient.from_stops([(0, "red"), (1, "blue", 0.5)])
        >>> len(g), g[1].get("stop-opacity")
        (2, 0.5)
        """
        gradient = cls(**kwargs)
        for spec in stops:
            gradient.add_stop(*spec)
        return gradient


class LinearGradient(Gradient, tag="linearGradient"):
    """``<linearGradient>``: a gradient along a line.

    Parameters
    ----------
    *stops : Stop
        Color stops.
    x1, y1, x2, y2 : length, optional
        The gradient vector.
    gradient_units : {"objectBoundingBox", "userSpaceOnUse"}, optional
        Coordinate system of the vector.
    spread_method : {"pad", "reflect", "repeat"}, optional
        What happens beyond the ends of the vector.
    **kwargs
        ``transform``, ``href`` and other presentation, core and SVG attributes
        in Python spelling.

    See Also
    --------
    RadialGradient : Gradient around a center.

    Examples
    --------
    >>> str(LinearGradient(Stop(0, "red"), x2=1))
    '<linearGradient x2="1"><stop offset="0" stop-color="red"/></linearGradient>'
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
        """Box spanned by the gradient vector.

        Returns
        -------
        BBox or None
            The unit box for ``objectBoundingBox`` units, otherwise the box
            around the vector's end points.

        Examples
        --------
        >>> LinearGradient(x1=0, y1=0, x2=10, y2=5, gradient_units="userSpaceOnUse").local_bbox().width
        10.0
        """
        box = self._units_bbox("gradientUnits")
        if box is not None:
            return box
        x1, y1, x2, y2 = (user_units(self.get(n, d)) for n, d in (("x1", 0), ("y1", 0), ("x2", "100%"), ("y2", 0)))
        return BBox.from_points([(x1, y1), (x2, y2)])

    @classmethod
    def horizontal(cls, *colors: Color | str, **kwargs: Any) -> Self:
        """Create an evenly spaced left-to-right gradient.

        Parameters
        ----------
        *colors : Color or str
            The stop colors.
        **kwargs
            Further attributes of the gradient.

        Returns
        -------
        LinearGradient
            A gradient from ``(0, 0)`` to ``(1, 0)`` in bounding-box units.

        Examples
        --------
        >>> LinearGradient.horizontal("red", "blue").get("x2")
        1
        """
        return cls.from_colors(colors, x1=0, y1=0, x2=1, y2=0, **kwargs)

    @classmethod
    def vertical(cls, *colors: Color | str, **kwargs: Any) -> Self:
        """Create an evenly spaced top-to-bottom gradient.

        Parameters
        ----------
        *colors : Color or str
            The stop colors.
        **kwargs
            Further attributes of the gradient.

        Returns
        -------
        LinearGradient
            A gradient from ``(0, 0)`` to ``(0, 1)`` in bounding-box units.

        Examples
        --------
        >>> LinearGradient.vertical("red", "blue").get("y2")
        1
        """
        return cls.from_colors(colors, x1=0, y1=0, x2=0, y2=1, **kwargs)


class RadialGradient(Gradient, tag="radialGradient"):
    """``<radialGradient>``: a gradient around a center.

    Parameters
    ----------
    *stops : Stop
        Color stops.
    cx, cy : length, optional
        Center of the outer circle.
    r : length, optional
        Radius of the outer circle.
    fx, fy : length, optional
        Focal point.
    gradient_units : {"objectBoundingBox", "userSpaceOnUse"}, optional
        Coordinate system of the circle.
    spread_method : {"pad", "reflect", "repeat"}, optional
        What happens beyond the circle.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    LinearGradient : Gradient along a line.

    Examples
    --------
    >>> str(RadialGradient(cx=0.5, cy=0.5, r=0.5))
    '<radialGradient cx="0.5" cy="0.5" r="0.5"/>'
    """

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
        """Box of the gradient's outer circle.

        Returns
        -------
        BBox or None
            The unit box for ``objectBoundingBox`` units, otherwise the circle's box.

        Examples
        --------
        >>> RadialGradient(cx=5, cy=5, r=2, gradient_units="userSpaceOnUse").local_bbox().width
        4.0
        """
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
    """``<pattern>``: a tile of graphics used as paint.

    Parameters
    ----------
    *children : Element
        The graphics of one tile.
    pattern_units : {"objectBoundingBox", "userSpaceOnUse"}, optional
        Coordinate system of ``x``, ``y``, ``width`` and ``height``.
    pattern_content_units : {"objectBoundingBox", "userSpaceOnUse"}, optional
        Coordinate system of the tile's content.
    **kwargs
        ``x``, ``y``, ``width``, ``height``, ``view_box``, ``transform`` and other
        presentation, core and SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> p = Pattern(svg.Circle(2, 2, 2), width=4, height=4, pattern_units="userSpaceOnUse")
    >>> p.local_bbox().width
    4.0
    """

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
        """Box of one tile from its ``x``, ``y``, ``width`` and ``height``.

        Returns
        -------
        BBox or None
            The tile rectangle.

        Examples
        --------
        >>> Pattern(width=10, height=10, pattern_units="userSpaceOnUse").local_bbox().height
        10.0
        """
        return positioned_bbox(self)
