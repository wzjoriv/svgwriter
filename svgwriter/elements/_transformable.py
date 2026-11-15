"""``Transformable``: the ``t`` transform, the anchor and the move/rotate/scale/skew methods."""

from __future__ import annotations

from numbers import Real
from typing import Any, ClassVar, TypeVar

import numpy as np

from ..path.data import BBox
from ..transform.matrix import IDENTITY, Matrix, Point
from ..transform.ops import TransformOp
from ..transform.transform import Transform, TransformLike, as_transform
from .base import Child, Element

__all__ = ["PointLike", "Transformable", "children_bbox", "offset"]

PointLike = tuple[float, float] | Point
E = TypeVar("E", bound="Transformable")
_TRANSFORMS = (Transform, TransformOp, Matrix)


def offset(value: object) -> tuple[float, float] | None:
    """*value* as an ``(x, y)`` pair: a number broadcasts, a 2-sequence of numbers is taken as is."""
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "iuf" or value.shape not in ((), (2,)):
            return None
        value = value.item() if value.shape == () else tuple(value.tolist())
    if isinstance(value, Real) and not isinstance(value, bool):
        return (float(value), float(value))
    if isinstance(value, (tuple, list, Point)) and len(value) == 2 and all(isinstance(v, Real) for v in value):
        return (float(value[0]), float(value[1]))
    return None


def _as_matrix(value: TransformLike) -> Matrix:
    return value if isinstance(value, Matrix) else as_transform(value).to_matrix()


def children_bbox(element: Element) -> BBox | None:
    """Union of the children's :meth:`Transformable.bounds`."""
    result: BBox | None = None
    for child in element:
        box = child.bounds() if isinstance(child, Transformable) else None
        if box is not None:
            result = box if result is None else result.union(box)
    return result


class Transformable(Element):
    """An element placed by a transform.

    The element's own geometry attributes (``cx``, ``x``, ``d``, ...) are
    local coordinates and stay as written; every move goes through
    :attr:`t`. Rotation, scaling and skewing pivot on :attr:`anchor`.

    Parameters
    ----------
    t : Transform, Matrix or str, optional
        Initial transform (``transform=`` is accepted as an alias).
    anchor : (float, float), optional
        Pivot in local coordinates; the bounding-box centre when omitted.

    Examples
    --------
    >>> import svgwriter as svg
    >>> c = svg.circle(50, 50, 10).translate(10, 0).rotate(90)
    >>> str(c.t)
    'rotate(90 55 55)'
    >>> c.position
    Point(x=60.0, y=50.0)

    Notes
    -----
    ``t`` is one affine matrix. Every method multiplies into it (before it
    in the parent frame, after it with ``local=True``) instead of
    appending to a list; output is the shortest equivalent ``transform``.
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
        """Same as :attr:`t`, under the SVG attribute's name."""
        return self.t

    @transform.setter
    def transform(self, value: TransformLike | None) -> None:
        self.t = value

    def local_bbox(self) -> BBox | None:
        """Bounding box in local coordinates (before :attr:`t`), if known."""
        return None

    @property
    def anchor(self) -> Point:
        """Pivot in local coordinates; the bounding-box centre unless set.

        Assign ``None`` to go back to the centre.
        """
        if self._anchor is not None:
            return Point(*self._anchor)
        box = self.local_bbox()
        return box.center if box is not None else Point(0.0, 0.0)

    @anchor.setter
    def anchor(self, value: PointLike | None) -> None:
        self._anchor = None if value is None else (float(value[0]), float(value[1]))

    @property
    def position(self) -> Point:
        """The anchor in parent coordinates; assign to move the element there."""
        return self.t.apply(*self.anchor)

    @position.setter
    def position(self, value: PointLike) -> None:
        here = self.position
        self.translate(value[0] - here.x, value[1] - here.y)

    def place(self: E, x: float, y: float) -> E:
        """Translate so the anchor lands on ``(x, y)`` in parent coordinates."""
        self.position = (x, y)
        return self

    def bounds(self) -> BBox | None:
        """Bounding box in parent coordinates (after :attr:`t`)."""
        box = self.local_bbox()
        if box is None:
            return None
        m = self.t
        corners = [(box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
                   (box.x + box.width, box.y + box.height)]
        return BBox.from_points(m.apply(*p) for p in corners)

    def _pivot(self, about: PointLike | None, local: bool) -> Point:
        if about is not None:
            return Point(float(about[0]), float(about[1]))
        return self.anchor if local else self.position

    def _compose(self: E, op: Matrix, local: bool, about: PointLike | None = None, pivot: bool = True) -> E:
        if pivot:
            p = self._pivot(about, local)
            op = Matrix.translate(p.x, p.y) @ op @ Matrix.translate(-p.x, -p.y)
        self.t = self.t @ op if local else op @ self.t
        return self

    def translate(self: E, dx: float, dy: float = 0.0, *, local: bool = False) -> E:
        """Move by ``(dx, dy)`` and return ``self``.

        Parameters
        ----------
        dx, dy : float
            Offset in user units.
        local : bool
            Measure along the element's own (rotated, scaled) axes instead
            of the parent's.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 2, 2).rotate(90).translate(10, 0).position
        Point(x=11.0, y=1.0)
        """
        return self._compose(Matrix.translate(dx, dy), local, pivot=False)

    def rotate(self: E, degrees: float, *, about: PointLike | None = None, local: bool = False) -> E:
        """Rotate by *degrees* (clockwise on screen) and return ``self``.

        Parameters
        ----------
        degrees : float
            Angle; positive turns from +x towards +y.
        about : (float, float), optional
            Pivot; in parent coordinates, or local ones with *local*.
            Defaults to the :attr:`anchor`.
        local : bool
            Compose in the element's own frame.
        """
        return self._compose(Matrix.rotate(degrees), local, about)

    def scale(
        self: E, sx: float, sy: float | None = None, *, about: PointLike | None = None, local: bool = False
    ) -> E:
        """Scale by *sx* and *sy* (default *sx*) about the anchor and return ``self``.

        Parameters
        ----------
        sx, sy : float
            Factors along x and y; negative values mirror.
        about : (float, float), optional
            Fixed point instead of the :attr:`anchor`.
        local : bool
            Scale along the element's own axes instead of the parent's.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.circle(50, 50, 10).scale(2).bounds()
        BBox(x=30.0, y=30.0, width=40.0, height=40.0)
        """
        return self._compose(Matrix.scale(sx, sy), local, about)

    def skew(
        self: E, x_degrees: float = 0.0, y_degrees: float = 0.0, *, about: PointLike | None = None,
        local: bool = False,
    ) -> E:
        """Skew along x then y by angles in degrees about the anchor and return ``self``."""
        return self._compose(Matrix.skew_y(y_degrees) @ Matrix.skew_x(x_degrees), local, about)

    def flip_x(self: E, *, about: PointLike | None = None, local: bool = False) -> E:
        """Mirror left-right (across the vertical line through the anchor) and return ``self``."""
        return self.scale(-1, 1, about=about, local=local)

    def flip_y(self: E, *, about: PointLike | None = None, local: bool = False) -> E:
        """Mirror top-bottom (across the horizontal line through the anchor) and return ``self``."""
        return self.scale(1, -1, about=about, local=local)

    def apply(self: E, transform: TransformLike, *, local: bool = False) -> E:
        """Compose an arbitrary transform (no pivot), in the parent frame unless *local*."""
        return self._compose(_as_matrix(transform), local, pivot=False)

    def reset(self: E) -> E:
        """Drop the transform and return ``self``."""
        self.t = None
        return self

    def _transformed_by(self: E, operator: str, operand: object, in_place: bool) -> E:
        """Apply an arithmetic operator; ``NotImplemented`` when *operand* does not fit."""
        target = self if in_place else self.copy()
        if operator == "@":
            if isinstance(operand, Real):
                return target.rotate(float(operand))
            if isinstance(operand, (*_TRANSFORMS, str)):
                return target.apply(operand, local=True)  # type: ignore[arg-type]
            return NotImplemented
        pair = offset(operand)
        if pair is None:
            if operator == "*" and isinstance(operand, (*_TRANSFORMS, str)):
                raise TypeError("use M @ element (parent frame) or element @ M (local frame) to apply a transform")
            return NotImplemented
        x, y = pair
        if operator == "+":
            return target.translate(x, y)
        if operator == "-":
            return target.translate(-x, -y)
        if operator == "*":
            return target.scale(x, y)
        if x == 0 or y == 0:
            raise ZeroDivisionError("cannot scale an element by 1/0")
        return target.scale(1 / x, 1 / y)

    def __add__(self, other: Any) -> Any:
        """``el + (dx, dy)``: a translated copy; ``el + other_element`` groups them."""
        result = self._transformed_by("+", other, in_place=False)
        return super().__add__(other) if result is NotImplemented else result

    def __radd__(self, other: Any) -> Any:
        result = self._transformed_by("+", other, in_place=False)
        return super().__radd__(other) if result is NotImplemented else result

    def __iadd__(self, other: Any) -> Any:
        """``el += (dx, dy)`` moves in place; containers still append with ``+= element``."""
        result = self._transformed_by("+", other, in_place=True)
        if result is not NotImplemented:
            return result
        parent = super()
        return parent.__iadd__(other) if hasattr(parent, "__iadd__") else NotImplemented  # type: ignore[misc]

    def __sub__(self, other: Any) -> Any:
        """``el - (dx, dy)``: a copy translated by the negated offset."""
        return self._transformed_by("-", other, in_place=False)

    def __isub__(self, other: Any) -> Any:
        return self._transformed_by("-", other, in_place=True)

    def __mul__(self: E, factor: float | tuple[float, float]) -> E:
        """``el * k`` or ``el * (sx, sy)``: a copy scaled about the anchor."""
        return self._transformed_by("*", factor, in_place=False)

    def __rmul__(self: E, factor: float) -> E:
        return self._transformed_by("*", factor, in_place=False)

    def __imul__(self: E, factor: float | tuple[float, float]) -> E:
        return self._transformed_by("*", factor, in_place=True)

    def __truediv__(self: E, divisor: float | tuple[float, float]) -> E:
        """``el / k``: a copy scaled by ``1/k`` about the anchor."""
        return self._transformed_by("/", divisor, in_place=False)

    def __itruediv__(self: E, divisor: float | tuple[float, float]) -> E:
        return self._transformed_by("/", divisor, in_place=True)

    def __matmul__(self: E, operand: TransformLike | float) -> E:
        """``el @ degrees`` rotates a copy about the anchor; ``el @ M`` applies *M* in the local frame."""
        return self._transformed_by("@", operand, in_place=False)

    def __imatmul__(self: E, operand: TransformLike | float) -> E:
        return self._transformed_by("@", operand, in_place=True)

    def __rmatmul__(self: E, transform: TransformLike) -> E:
        """``M @ el``: a copy with *M* applied in the parent frame."""
        if not isinstance(transform, (*_TRANSFORMS, str)):
            return NotImplemented
        return self.copy().apply(transform)
