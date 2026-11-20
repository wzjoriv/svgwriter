"""
Alternate constructors for ``<rect>``: squares, boxes, corners and centers.
"""

from __future__ import annotations

from typing import Any

from ..._internal._typing import Self
from ...pathdata.data import BBox

__all__ = ["RectConstructors"]


class RectConstructors:
    """``square``, ``from_bbox``, ``from_corners`` and ``from_center``; mixed into :class:`~svgwriter.elements.shapes.Rect`."""

    __slots__ = ()

    @classmethod
    def square(cls, size: float, *, center: tuple[float, float] | None = None, **kwargs: Any) -> Self:
        """Create a square of a given side.

        The square sits at the origin unless `center` is given.

        Parameters
        ----------
        size : float
            Side length.
        center : tuple of float, optional
            Center ``(x, y)`` of the square. Defaults to None, placing the
            top-left corner at the origin.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Rect
            The new rectangle.

        See Also
        --------
        from_center : Rectangles that are not square.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Rect.square(10, center=(10, 10)))
        '<rect x="5" y="5" width="10" height="10"/>'
        """
        if center is not None:
            return cls.from_center(center, (size, size), **kwargs)
        return cls(width=size, height=size, **kwargs)

    @classmethod
    def from_bbox(cls, box: BBox, **kwargs: Any) -> Self:
        """Create a rectangle covering a bounding box.

        Parameters
        ----------
        box : BBox
            The area to cover.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Rect
            The new rectangle.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Rect.from_bbox(svg.BBox(1, 2, 3, 4)))
        '<rect x="1" y="2" width="3" height="4"/>'
        """
        return cls(box.x, box.y, box.width, box.height, **kwargs)

    @classmethod
    def from_corners(cls, first: tuple[float, float], second: tuple[float, float], **kwargs: Any) -> Self:
        """Create the rectangle spanned by two opposite corners.

        The corners may be given in any order.

        Parameters
        ----------
        first, second : tuple of float
            Opposite corners ``(x, y)``.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Rect
            The new rectangle.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Rect.from_corners((30, 40), (10, 20)))
        '<rect x="10" y="20" width="20" height="20"/>'
        """
        (x0, y0), (x1, y1) = first, second
        return cls(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), **kwargs)

    @classmethod
    def from_center(cls, center: tuple[float, float], size: tuple[float, float], **kwargs: Any) -> Self:
        """Create a rectangle of a given size around a center point.

        Parameters
        ----------
        center : tuple of float
            Center ``(x, y)``.
        size : tuple of float
            ``(width, height)``.
        **kwargs
        Presentation, core and other SVG attributes in Python spelling.

        Returns
        -------
        Rect
            The new rectangle.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.Rect.from_center((50, 50), (20, 10), rx=2))
        '<rect x="40" y="45" width="20" height="10" rx="2"/>'
        """
        (cx, cy), (w, h) = center, size
        return cls(cx - w / 2, cy - h / 2, w, h, **kwargs)
