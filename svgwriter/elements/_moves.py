"""
Transform methods for transformable elements: translate, rotate, scale, skew, flips and operators.
"""

from __future__ import annotations

from numbers import Real
from typing import TYPE_CHECKING, Any

from ..transform.matrix import Matrix, Point
from ..transform.ops import TransformOp
from ..transform.transform import Transform, TransformLike, as_transform

if TYPE_CHECKING:
    from ._transformable import E, PointLike

__all__ = ["TransformMethods"]

_TRANSFORMS = (Transform, TransformOp, Matrix)


def _as_matrix(value: TransformLike) -> Matrix:
    return value if isinstance(value, Matrix) else as_transform(value).to_matrix()


class TransformMethods:
    """Translate, rotate, scale, skew and operators; mixed into :class:`~svgwriter.elements._transformable.Transformable`."""

    __slots__ = ()

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

        The offset is added to the transform, in the parent frame unless *local*.

        Parameters
        ----------
        dx, dy : float
            Offset in user units. *dy* defaults to 0.
        local : bool, optional
            Measure along the element's own (rotated, scaled) axes instead
            of the parent's. Defaults to False.

        Returns
        -------
        Transformable
            This element.

        See Also
        --------
        place : Move the anchor to an absolute position.

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
        local : bool, optional
            Compose in the element's own frame. Defaults to False.

        Returns
        -------
        Transformable
            This element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 10).rotate(90).bounds()
        BBox(x=0.0, y=0.0, width=10.0, height=10.0)
        """
        return self._compose(Matrix.rotate(degrees), local, about)

    def scale(
        self: E, sx: float, sy: float | None = None, *, about: PointLike | None = None, local: bool = False
    ) -> E:
        """Scale by *sx* and *sy* (default *sx*) about the anchor and return ``self``.

        Parameters
        ----------
        sx, sy : float
            Factors along x and y; negative values mirror. *sy* defaults to *sx*.
        about : (float, float), optional
            Fixed point. Defaults to the :attr:`anchor`.
        local : bool, optional
            Scale along the element's own axes instead of the parent's. Defaults to False.

        Returns
        -------
        Transformable
            This element.

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
        """Skew along x then y by angles in degrees about the anchor and return ``self``.

        Parameters
        ----------
        x_degrees, y_degrees : float, optional
            Skew angles along x and y. Defaults to 0.
        about : (float, float), optional
            Fixed point. Defaults to the :attr:`anchor`.
        local : bool, optional
            Compose in the element's own frame. Defaults to False.

        Returns
        -------
        Transformable
            This element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 10).skew(45).bounds()
        BBox(x=-5.0, y=0.0, width=20.0, height=10.0)
        """
        return self._compose(Matrix.skew_y(y_degrees) @ Matrix.skew_x(x_degrees), local, about)

    def flip_x(self: E, *, about: PointLike | None = None, local: bool = False) -> E:
        """Mirror left-right (across the vertical line through the anchor) and return ``self``.

        Parameters
        ----------
        about : (float, float), optional
            Point on the mirror line. Defaults to the :attr:`anchor`.
        local : bool, optional
            Compose in the element's own frame. Defaults to False.

        Returns
        -------
        Transformable
            This element.

        See Also
        --------
        flip_y : Mirror top-bottom.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 10).flip_x(about=(0, 0)).bounds()
        BBox(x=-10.0, y=0.0, width=10.0, height=10.0)
        """
        return self.scale(-1, 1, about=about, local=local)

    def flip_y(self: E, *, about: PointLike | None = None, local: bool = False) -> E:
        """Mirror top-bottom (across the horizontal line through the anchor) and return ``self``.

        Parameters
        ----------
        about : (float, float), optional
            Point on the mirror line. Defaults to the :attr:`anchor`.
        local : bool, optional
            Compose in the element's own frame. Defaults to False.

        Returns
        -------
        Transformable
            This element.

        See Also
        --------
        flip_x : Mirror left-right.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 10, 10).flip_y(about=(0, 0)).bounds()
        BBox(x=0.0, y=-10.0, width=10.0, height=10.0)
        """
        return self.scale(1, -1, about=about, local=local)

    def apply(self: E, transform: TransformLike, *, local: bool = False) -> E:
        """Compose an arbitrary transform (no pivot), in the parent frame unless *local*.

        Parameters
        ----------
        transform : Transform, Matrix or str
            The transform to compose.
        local : bool, optional
            Apply in the element's own frame. Defaults to False.

        Returns
        -------
        Transformable
            This element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1).apply("translate(4 5)").position
        Point(x=4.5, y=5.5)
        """
        return self._compose(_as_matrix(transform), local, pivot=False)

    def reset(self: E) -> E:
        """Drop the transform and return ``self``.

        Returns
        -------
        Transformable
            This element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1).translate(3, 3).reset().t.is_identity
        True
        """
        self.t = None
        return self

    def _transformed_by(self: E, operator: str, operand: object, in_place: bool) -> E:
        """Apply an arithmetic operator; ``NotImplemented`` when *operand* does not fit."""
        from ._transformable import offset

        target = self if in_place else self.clone()
        if operator == "@":
            from ..attributes.angle import Angle

            if isinstance(operand, (Real, Angle)):
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
        return self.clone().apply(transform)
