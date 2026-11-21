"""
Clipping, masking and markers.
"""

from __future__ import annotations

from typing import Any, Literal, TypeAlias

from ..._internal._typing import Units
from ...attributes.length import LengthLike
from ...pathdata.data import BBox, PathData
from .._behavior import (
    ConditionalAttributes,
    CoreAttributes,
    ExternalResourcesAttribute,
    FitToViewBox,
    PathOperand,
    Positioned,
    PresentationAttributes,
    Transformable,
    children_bbox,
    union_outline,
)
from ..core import Category, Child, GraphicsContainer

__all__ = ["ClipPath", "Marker", "MarkerOrient", "Mask"]

MarkerOrient: TypeAlias = float | Literal["auto"]


class ClipPath(
    PathOperand,
    Transformable,
    PresentationAttributes,
    ConditionalAttributes,
    ExternalResourcesAttribute,
    CoreAttributes,
    GraphicsContainer,
    tag="clipPath",
    category=Category.CONTAINER,
):
    """``<clipPath>``: shapes whose union is the clipping region.

    Parameters
    ----------
    *children : Element
        Shapes, text and ``use`` elements that define the region.
    clip_path_units : {"userSpaceOnUse", "objectBoundingBox"}, optional
        Coordinate system of the content.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Mask : Soft, luminance-based masking.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(ClipPath(svg.Rect(0, 0, 10, 10), id="c"))
    '<clipPath id="c"><rect x="0" y="0" width="10" height="10"/></clipPath>'
    """

    def __init__(self, *children: Child, clip_path_units: Units | None = None, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._assign(clip_path_units=clip_path_units)

    def local_bbox(self) -> BBox | None:
        """Box around the clipping shapes.

        Returns
        -------
        BBox or None
            ``None`` when the clip path is empty.

        Examples
        --------
        >>> import svgwriter as svg
        >>> ClipPath(svg.Rect(0, 0, 10, 20)).local_bbox().height
        20.0
        """
        return children_bbox(self)

    def local_outline(self) -> PathData:
        """Union of the children's outlines.

        Returns
        -------
        PathData
            The clipping region as path data.

        Examples
        --------
        >>> import svgwriter as svg
        >>> len(ClipPath(svg.Rect(0, 0, 10, 10)).local_outline()) > 0
        True
        """
        return union_outline(self)


class Mask(
    Positioned,
    PresentationAttributes,
    ConditionalAttributes,
    ExternalResourcesAttribute,
    CoreAttributes,
    GraphicsContainer,
    tag="mask",
    category=Category.CONTAINER,
):
    """``<mask>``: luminance of its content becomes the alpha mask.

    Parameters
    ----------
    *children : Element
        The graphics whose luminance defines the mask.
    mask_units : {"objectBoundingBox", "userSpaceOnUse"}, optional
        Coordinate system of ``x``, ``y``, ``width`` and ``height``.
    mask_content_units : {"userSpaceOnUse", "objectBoundingBox"}, optional
        Coordinate system of the content.
    **kwargs
        ``x``, ``y``, ``width``, ``height`` and other presentation, core and SVG
        attributes in Python spelling.

    See Also
    --------
    ClipPath : Hard-edged clipping region.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(Mask(svg.Rect(0, 0, 10, 10), id="m", mask_units="userSpaceOnUse"))
    '<mask id="m" maskUnits="userSpaceOnUse"><rect x="0" y="0" width="10" height="10"/></mask>'
    """

    def __init__(
        self,
        *children: Child,
        mask_units: Units | None = None,
        mask_content_units: Units | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        self._assign(mask_units=mask_units, mask_content_units=mask_content_units)


class Marker(
    FitToViewBox,
    PresentationAttributes,
    ExternalResourcesAttribute,
    CoreAttributes,
    GraphicsContainer,
    tag="marker",
    category=Category.CONTAINER,
):
    """``<marker>``: arrowheads and other symbols at path vertices.

    Parameters
    ----------
    *children : Element
        The marker graphics.
    ref_x, ref_y : float, optional
        The point aligned with the vertex. Defaults to 0.
    marker_width, marker_height : length, optional
        Viewport size.
    marker_units : {"strokeWidth", "userSpaceOnUse"}, optional
        Coordinate system of the size.
    orient : float or "auto", optional
        Rotation; ``"auto"`` follows the path direction.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Path : A shape that can carry markers.

    Examples
    --------
    >>> import svgwriter as svg
    >>> m = Marker(svg.Circle(0, 0, 2), ref_x=1, marker_width=4, marker_height=4, orient="auto")
    >>> m.get("orient")
    'auto'
    """

    def __init__(
        self,
        *children: Child,
        ref_x: float = 0,
        ref_y: float = 0,
        marker_width: LengthLike | None = None,
        marker_height: LengthLike | None = None,
        marker_units: Literal["strokeWidth", "userSpaceOnUse"] | None = None,
        orient: MarkerOrient | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        self._assign(
            ref_x=ref_x,
            ref_y=ref_y,
            marker_units=marker_units,
            marker_width=marker_width,
            marker_height=marker_height,
            orient=orient,
        )
