"""
``rect``, ``circle``, ``ellipse`` and ``line``.
"""

from __future__ import annotations

import math
from typing import Any, ClassVar

from ..._internal._typing import Self
from ...attributes.descriptors import LengthAttr
from ...attributes.length import LengthLike
from ...pathdata.builder import PathBuilder
from ...pathdata.data import BBox, PathData
from ._base import Shape, user_units
from ._rectbuild import RectConstructors

__all__ = ["Circle", "Ellipse", "Line", "Rect"]


def _ellipse_outline(cx: float, cy: float, rx: float, ry: float) -> PathData:
    return (
        PathBuilder()
        .move_to(cx - rx, cy)
        .arc_to(rx, ry, 0, False, True, cx + rx, cy)
        .arc_to(rx, ry, 0, False, True, cx - rx, cy)
        .close()
        .build()
    )


class Rect(RectConstructors, Shape, tag="rect"):
    """``<rect>``: an axis-aligned rectangle with optional rounded corners.

    Giving only one of `rx` and `ry` uses it for both, and radii are clamped
    to half the width and height, as SVG specifies.

    Parameters
    ----------
    x, y : length, optional
        Top-left corner. Defaults to 0.
    width, height : length, optional
        Size. Defaults to 0.
    rx, ry : length, optional
        Corner radii. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Circle : A circle from its center and radius.
    Path : Arbitrary outlines.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Rect(1, 2, 3, 4, rx=1))
    '<rect x="1" y="2" width="3" height="4" rx="1"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"x", "y", "width", "height", "rx", "ry"})
    x = LengthAttr()
    y = LengthAttr()
    width = LengthAttr()
    height = LengthAttr()
    rx = LengthAttr()
    ry = LengthAttr()

    def __init__(
        self,
        x: LengthLike = 0,
        y: LengthLike = 0,
        width: LengthLike = 0,
        height: LengthLike = 0,
        *,
        rx: LengthLike | None = None,
        ry: LengthLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(x=x, y=y, width=width, height=height, rx=rx, ry=ry)

    @property
    def bbox(self) -> BBox:
        """Geometric bounding box in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Rect(1, 2, 3, 4).bbox
        BBox(x=1.0, y=2.0, width=3.0, height=4.0)
        """
        return BBox(user_units(self.x), user_units(self.y), user_units(self.width), user_units(self.height))

    def corner_radii(self) -> tuple[float, float]:
        """Return the effective corner radii.

        A missing radius takes the other's value, and each is clamped to half
        the corresponding side.

        Returns
        -------
        tuple of float
            The effective ``(rx, ry)`` in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Rect(0, 0, 10, 10, rx=20).corner_radii()
        (5.0, 5.0)
        """
        rx = None if self.rx is None else user_units(self.rx)
        ry = None if self.ry is None else user_units(self.ry)
        rx = ry if rx is None else rx
        ry = rx if ry is None else ry
        box = self.bbox
        return min(rx or 0.0, box.width / 2), min(ry or 0.0, box.height / 2)

    def local_outline(self) -> PathData:
        x, y, w, h = self.bbox
        rx, ry = self.corner_radii()
        builder = PathBuilder().move_to(x + rx, y).horizontal_to(x + w - rx)
        if rx and ry:
            builder.arc_to(rx, ry, 0, False, True, x + w, y + ry)
        builder.vertical_to(y + h - ry)
        if rx and ry:
            builder.arc_to(rx, ry, 0, False, True, x + w - rx, y + h)
        builder.horizontal_to(x + rx)
        if rx and ry:
            builder.arc_to(rx, ry, 0, False, True, x, y + h - ry)
        if rx and ry:
            builder.vertical_to(y + ry)
            builder.arc_to(rx, ry, 0, False, True, x + rx, y)
        return builder.close().build()


class Circle(Shape, tag="circle"):
    """``<circle>``: a circle from its center and radius.

    Parameters
    ----------
    cx, cy : length, optional
        Center. Defaults to 0.
    r : length, optional
        Radius. Defaults to 0.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Ellipse : Different horizontal and vertical radii.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Circle(5, 5, 3))
    '<circle cx="5" cy="5" r="3"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"cx", "cy", "r"})
    cx = LengthAttr()
    cy = LengthAttr()
    r = LengthAttr()

    def __init__(self, cx: LengthLike = 0, cy: LengthLike = 0, r: LengthLike = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(cx=cx, cy=cy, r=r)

    @classmethod
    def from_bbox(cls, box: BBox, **kwargs: Any) -> Self:
        """Create the largest circle centered in a bounding box.

        Parameters
        ----------
        box : BBox
            The area to fit.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Circle
            The new circle.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Circle.from_bbox(svg.BBox(0, 0, 10, 20)))
        '<circle cx="5" cy="10" r="5"/>'
        """
        center = box.center
        return cls(center.x, center.y, min(box.width, box.height) / 2.0, **kwargs)

    @property
    def area(self) -> float:
        """Enclosed area in square user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> round(svg.Circle(0, 0, 1).area, 4)
        3.1416
        """
        return math.pi * user_units(self.r) ** 2

    @property
    def bbox(self) -> BBox:
        """Geometric bounding box in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Circle(0, 0, 2).bbox
        BBox(x=-2.0, y=-2.0, width=4.0, height=4.0)
        """
        cx, cy, r = user_units(self.cx), user_units(self.cy), user_units(self.r)
        return BBox(cx - r, cy - r, 2 * r, 2 * r)

    def local_outline(self) -> PathData:
        r = user_units(self.r)
        return _ellipse_outline(user_units(self.cx), user_units(self.cy), r, r)


class Ellipse(Shape, tag="ellipse"):
    """``<ellipse>``: an ellipse from its center and two radii.

    Parameters
    ----------
    cx, cy : length, optional
        Center. Defaults to 0.
    rx, ry : length, optional
        Horizontal and vertical radii. Defaults to 0.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Circle : Equal radii.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Ellipse(5, 5, 3, 2))
    '<ellipse cx="5" cy="5" rx="3" ry="2"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"cx", "cy", "rx", "ry"})
    cx = LengthAttr()
    cy = LengthAttr()
    rx = LengthAttr()
    ry = LengthAttr()

    def __init__(
        self, cx: LengthLike = 0, cy: LengthLike = 0, rx: LengthLike = 0, ry: LengthLike = 0, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.update(cx=cx, cy=cy, rx=rx, ry=ry)

    @classmethod
    def from_bbox(cls, box: BBox, **kwargs: Any) -> Self:
        """Create the ellipse inscribed in a bounding box.

        Parameters
        ----------
        box : BBox
            The area to fill.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Ellipse
            The new ellipse.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Ellipse.from_bbox(svg.BBox(0, 0, 10, 20)))
        '<ellipse cx="5" cy="10" rx="5" ry="10"/>'
        """
        center = box.center
        return cls(center.x, center.y, box.width / 2.0, box.height / 2.0, **kwargs)

    @property
    def bbox(self) -> BBox:
        """Geometric bounding box in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Ellipse(5, 5, 3, 2).bbox
        BBox(x=2.0, y=3.0, width=6.0, height=4.0)
        """
        cx, cy, rx, ry = (user_units(v) for v in (self.cx, self.cy, self.rx, self.ry))
        return BBox(cx - rx, cy - ry, 2 * rx, 2 * ry)

    def local_outline(self) -> PathData:
        return _ellipse_outline(*(user_units(v) for v in (self.cx, self.cy, self.rx, self.ry)))


class Line(Shape, tag="line"):
    """``<line>``: a straight segment between two points.

    Parameters
    ----------
    x1, y1 : length, optional
        Start point. Defaults to 0.
    x2, y2 : length, optional
        End point. Defaults to 0.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Polyline : Several connected segments.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Line(0, 0, 3, 4))
    '<line x1="0" y1="0" x2="3" y2="4"/>'
    """

    geometry_attributes: ClassVar[frozenset[str]] = frozenset({"x1", "y1", "x2", "y2"})
    x1 = LengthAttr()
    y1 = LengthAttr()
    x2 = LengthAttr()
    y2 = LengthAttr()

    def __init__(
        self, x1: LengthLike = 0, y1: LengthLike = 0, x2: LengthLike = 0, y2: LengthLike = 0, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.update(x1=x1, y1=y1, x2=x2, y2=y2)

    @property
    def length(self) -> float:
        """Distance between the end points in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Line(0, 0, 3, 4).length
        5.0
        """
        return math.hypot(user_units(self.x2) - user_units(self.x1), user_units(self.y2) - user_units(self.y1))

    @property
    def bbox(self) -> BBox:
        """Geometric bounding box in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Line(0, 0, 3, 4).bbox
        BBox(x=0.0, y=0.0, width=3.0, height=4.0)
        """
        return BBox.from_points([(user_units(self.x1), user_units(self.y1)), (user_units(self.x2), user_units(self.y2))])

    def local_outline(self) -> PathData:
        return PathBuilder().move_to(user_units(self.x1), user_units(self.y1)).line_to(user_units(self.x2), user_units(self.y2)).build()
