"""``Transformable``: the ``t`` transform, the anchor and the move/rotate/scale/skew methods."""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Real
from typing import Any, ClassVar, TypeVar

from ..path.data import BBox
from ..transform.matrix import Matrix, Point
from ..transform.ops import Rotate, Scale, SkewX, SkewY, TransformOp, Translate
from ..transform.transform import Transform, TransformLike, as_transform
from .base import Child, Element

__all__ = ["PointLike", "Transformable", "children_bbox"]

PointLike = tuple[float, float] | Point
E = TypeVar("E", bound="Transformable")
_TRANSFORMS = (Transform, TransformOp, Matrix)


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
    'rotate(90 60 50) translate(10)'
    >>> c.position
    Point(x=60.0, y=50.0)
    """

    transform_attribute: ClassVar[str] = "transform"
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
    def t(self) -> Transform:
        """The transform, as a copy; assign to replace it."""
        raw = self.attributes.get(self.transform_attribute)
        return Transform() if raw is None else Transform(as_transform(raw))

    @t.setter
    def t(self, value: TransformLike | None) -> None:
        transform = None if value is None else as_transform(value)
        if transform is None or not len(transform):
            self.attributes.pop(self.transform_attribute, None)
        else:
            self.attributes[self.transform_attribute] = Transform(transform)

    @property
    def transform(self) -> Transform:
        """Alias of :attr:`t`."""
        return self.t

    @transform.setter
    def transform(self, value: TransformLike | None) -> None:
        self.t = value

    @property
    def matrix(self) -> Matrix:
        """:attr:`t` collapsed to a single matrix."""
        return self.t.to_matrix()

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
        return self.matrix.apply(*self.anchor)

    @position.setter
    def position(self, value: PointLike) -> None:
        here = self.position
        self.translate(value[0] - here.x, value[1] - here.y)

    def place_at(self: E, x: float, y: float) -> E:
        """Translate so the anchor lands on ``(x, y)`` in parent coordinates."""
        self.position = (x, y)
        return self

    def bounds(self) -> BBox | None:
        """Bounding box in parent coordinates (after :attr:`t`)."""
        box = self.local_bbox()
        if box is None:
            return None
        m = self.matrix
        corners = [(box.x, box.y), (box.x + box.width, box.y), (box.x, box.y + box.height),
                   (box.x + box.width, box.y + box.height)]
        return BBox.from_points(m.apply(*p) for p in corners)

    def _pivot(self, about: PointLike | None, local: bool) -> Point:
        if about is not None:
            return Point(float(about[0]), float(about[1]))
        return self.anchor if local else self.position

    def _compose(self: E, ops: Sequence[TransformOp], local: bool) -> E:
        current = list(self.t)
        if local:
            current.extend(ops)
        elif len(ops) == 1 and isinstance(ops[0], Translate) and current and isinstance(current[0], Translate):
            first, op = current[0], ops[0]
            current[0] = Translate(first.tx + op.tx, (first.ty or 0.0) + (op.ty or 0.0))
        else:
            current[:0] = ops
        self.t = Transform(current)
        return self

    def _about(self: E, op: TransformOp, about: PointLike | None, local: bool) -> E:
        p = self._pivot(about, local)
        if p.x == 0 and p.y == 0:
            return self._compose([op], local)
        return self._compose([Translate(p.x, p.y), op, Translate(-p.x, -p.y)], local)

    def translate(self: E, dx: float, dy: float = 0.0, *, local: bool = False) -> E:
        """Move by ``(dx, dy)``; in parent axes unless *local*."""
        if dx == 0 and dy == 0:
            return self
        return self._compose([Translate(dx, dy)], local)

    def rotate(self: E, degrees: float, *, about: PointLike | None = None, local: bool = False) -> E:
        """Rotate by *degrees* (clockwise on screen) around the anchor or *about*."""
        p = self._pivot(about, local)
        return self._compose([Rotate(degrees, p.x, p.y)], local)

    def scale(
        self: E, sx: float, sy: float | None = None, *, about: PointLike | None = None, local: bool = False
    ) -> E:
        """Scale by *sx* (and *sy*, default *sx*) around the anchor or *about*."""
        return self._about(Scale(sx, sy), about, local)

    def skew(
        self: E, x_degrees: float = 0.0, y_degrees: float = 0.0, *, about: PointLike | None = None,
        local: bool = False,
    ) -> E:
        """Skew along x and/or y by angles in degrees around the anchor or *about*."""
        if x_degrees:
            self._about(SkewX(x_degrees), about, local)
        if y_degrees:
            self._about(SkewY(y_degrees), about, local)
        return self

    def apply(self: E, transform: TransformLike, *, local: bool = False) -> E:
        """Compose an arbitrary transform, in the parent frame unless *local*."""
        return self._compose(list(as_transform(transform)), local)

    def reset(self: E) -> E:
        """Drop the transform."""
        self.t = None
        return self

    def __matmul__(self: E, transform: TransformLike) -> E:
        """``el @ M``: a copy with *M* applied in the local frame."""
        if not isinstance(transform, (*_TRANSFORMS, str)):
            return NotImplemented
        return self.copy().apply(transform, local=True)

    def __rmatmul__(self: E, transform: TransformLike) -> E:
        """``M @ el``: a copy with *M* applied in the parent frame."""
        if not isinstance(transform, (*_TRANSFORMS, str)):
            return NotImplemented
        return self.copy().apply(transform)

    def __mul__(self: E, factor: float | tuple[float, float]) -> E:
        """``el * k``: a copy scaled by *k* (or ``(sx, sy)``) about the anchor."""
        if isinstance(factor, Real):
            return self.copy().scale(float(factor))
        if isinstance(factor, tuple) and len(factor) == 2:
            return self.copy().scale(*factor)
        if isinstance(factor, (*_TRANSFORMS, str)):
            raise TypeError("use M @ element (parent frame) or element @ M (local frame) to apply a transform")
        return NotImplemented

    def __rmul__(self: E, factor: float) -> E:
        return self.__mul__(factor)
