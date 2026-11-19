"""The ``Shape`` base class and shared helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ...pathdata.data import BBox
from .._geometry import PathOperand
from .._mixins import GraphicsElement
from .._viewport import user_units
from ..base import Category

__all__ = ["Shape", "parse_points", "user_units"]




def parse_points(text: str) -> list[tuple[float, float]]:
    """Parse the text of a ``points`` attribute into coordinate pairs.

    Commas and whitespace both separate numbers.

    Parameters
    ----------
    text : str
        SVG points text such as ``"0,0 10,5"``.

    Returns
    -------
    list of tuple of float
        The ``(x, y)`` pairs in order.

    Raises
    ------
    ValueError
        If `text` contains an odd number of coordinates.

    Examples
    --------
    >>> from svgwriter.elements.shapes._base import parse_points
    >>> parse_points("0,0 10,5")
    [(0.0, 0.0), (10.0, 5.0)]
    """
    numbers = [float(n) for n in text.replace(",", " ").split()]
    if len(numbers) % 2:
        raise ValueError(f"points need an even number of coordinates, got {len(numbers)}")
    return list(zip(numbers[::2], numbers[1::2], strict=False))


class Shape(PathOperand, GraphicsElement, ABC, category=Category.SHAPE):
    """Base class for the basic shapes and paths.

    Every shape converts to a ``<path>`` (:meth:`to_path`) and supports the
    geometric operators of :class:`~svgwriter.elements.PathOperand`.

    Parameters
    ----------
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Path : The general shape, built from path data.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Rect(0, 0, 10, 5).to_path())
    '<path d="M0 0 H10 V5 H0 V0 Z"/>'
    """

    @property
    @abstractmethod
    def bbox(self) -> BBox:
        """Geometric bounding box in user units, ignoring stroke and transform.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Circle(5, 5, 3).bbox
        BBox(x=2.0, y=2.0, width=6.0, height=6.0)
        """

    def local_bbox(self) -> BBox:
        """The geometric :attr:`bbox`."""
        return self.bbox
