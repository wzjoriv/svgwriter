"""
``Transformable``: the ``t`` transform, the anchor and the move/rotate/scale/skew methods.
"""

from __future__ import annotations

from numbers import Real
from typing import Any, ClassVar, TypeVar

import numpy as np

from ...pathdata.data import BBox
from ...transform.matrix import IDENTITY, Matrix, Point
from ...transform.transform import TransformLike, as_transform
from ..core import Child, Element
from ._moves import TransformMethods, _as_matrix
from ._placement import Placement

__all__ = ["PointLike", "Transformable", "children_bbox", "offset"]

PointLike = tuple[float, float] | Point
E = TypeVar("E", bound="Transformable")


def offset(value: object) -> tuple[float, float] | None:
    """*value* as an ``(x, y)`` pair: a number broadcasts, a 2-sequence of numbers is taken as is.

    Parameters
    ----------
    value : object
        A number, a pair of numbers or a one-dimensional numpy array of either.

    Returns
    -------
    tuple of float or None
        The pair, or None if *value* is not a number or a pair of numbers.

    Examples
    --------
    >>> from svgwriter.elements._behavior._transformable import offset
    >>> offset(3), offset((1, 2)), offset("x")
    ((3.0, 3.0), (1.0, 2.0), None)
    """
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "iuf" or value.shape not in ((), (2,)):
            return None
        value = value.item() if value.shape == () else tuple(value.tolist())
    if isinstance(value, Real) and not isinstance(value, bool):
        return (float(value), float(value))
    if isinstance(value, (tuple, list, Point)) and len(value) == 2 and all(isinstance(v, Real) for v in value):
        return (float(value[0]), float(value[1]))
    return None


def children_bbox(element: Element) -> BBox | None:
    """Union of the children's :meth:`Transformable.bounds` (a nested ``<svg>`` counts its viewport).

    Parameters
    ----------
    element : Element
        The parent whose children are measured.

    Returns
    -------
    BBox or None
        The combined box in the parent's coordinates, or None if no child has bounds.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.elements._behavior._transformable import children_bbox
    >>> children_bbox(svg.group(svg.rect(0, 0, 2, 2), svg.rect(5, 5, 1, 1)))
    BBox(x=0.0, y=0.0, width=6.0, height=6.0)
    """
    from ._viewport import positioned_bbox

    result: BBox | None = None
    for child in element:
        if isinstance(child, Transformable):
            box = child.bounds()
        elif child.tag == "svg":
            box = positioned_bbox(child)
        else:
            box = None
        if box is not None:
            result = box if result is None else result.union(box)
    return result


class Transformable(Placement, TransformMethods, Element):
    """An element placed by a transform.

    The element's own geometry attributes (``cx``, ``x``, ``d``, ...) are
    local coordinates and stay as written; every move goes through
    :attr:`t`. Rotation, scaling and skewing pivot on :attr:`anchor`.

    Parameters
    ----------
    t : Transform, Matrix or str, optional
        Initial transform (``transform=`` is accepted as an alias). Defaults to None.
    anchor : (float, float), optional
        Pivot in local coordinates. Defaults to the bounding-box centre.

    See Also
    --------
    svgwriter.elements._behavior.Convertible : Conversions and clipping on top of this class.

    Notes
    -----
    ``t`` is one affine matrix. Every method multiplies into it (before it
    in the parent frame, after it with ``local=True``) instead of
    appending to a list; output is the shortest equivalent ``transform``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> c = svg.circle(50, 50, 10).translate(10, 0).rotate(90)
    >>> str(c.t)
    'rotate(90 55 55)'
    >>> c.position
    Point(x=60.0, y=50.0)
    """

    transform_attribute: ClassVar[str] = "transform"
    __array_ufunc__ = None
    _anchor: tuple[float, float] | None = None

    def __init__(
        self,
        *args: Child,
        t: TransformLike | None = None,
        transform: TransformLike | None = None,
        anchor: PointLike | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if t is not None or transform is not None:
            self.t = t if t is not None else transform
        if anchor is not None:
            self.anchor = anchor

    @property
    def t(self) -> Matrix:
        """The transform as an affine :class:`~svgwriter.Matrix`; assign to replace it.

        Written to SVG as the shortest equivalent ``transform`` text.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1).translate(2, 3).t.apply(0, 0)
        Point(x=2.0, y=3.0)
        """
        raw = self.attributes.get(self.transform_attribute)
        if raw is None:
            return IDENTITY
        return raw if isinstance(raw, Matrix) else as_transform(raw).to_matrix()

    @t.setter
    def t(self, value: TransformLike | None) -> None:
        matrix = None if value is None else _as_matrix(value)
        if matrix is None or matrix.is_identity:
            self.attributes.pop(self.transform_attribute, None)
        else:
            self.attributes[self.transform_attribute] = matrix

    @property
    def transform(self) -> Matrix:
        """Same as :attr:`t`, under the SVG attribute's name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1).translate(2, 3)
        >>> r.transform == r.t
        True
        """
        return self.t

    @transform.setter
    def transform(self, value: TransformLike | None) -> None:
        self.t = value

    def local_bbox(self) -> BBox | None:
        """Bounding box in local coordinates (before :attr:`t`), if known.

        Returns
        -------
        BBox or None
            The box, or None when the element has no known extent. Subclasses override this.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(1, 2, 3, 4).local_bbox()
        BBox(x=1.0, y=2.0, width=3.0, height=4.0)
        """
        return None
