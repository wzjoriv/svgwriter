"""2-D affine matrices in SVG's ``[a b c d e f]`` layout."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, NamedTuple, overload

import numpy as np

from .._internal._constants import DEFAULT_PRECISION
from .._internal._speedups import format_number
from .._internal._typing import Matrix6

__all__ = ["IDENTITY", "Matrix", "Point"]

EPSILON: Final = 1e-12


class Point(NamedTuple):
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Matrix:
    """An affine transform ``[a c e; b d f; 0 0 1]``.

    Matrices compose with ``@`` in SVG order: ``m1 @ m2`` applies ``m2``
    first, matching ``transform="m1 m2"``.

    Examples
    --------
    >>> (Matrix.translate(10, 0) @ Matrix.scale(2)).apply(1, 1)
    Point(x=12.0, y=2.0)
    >>> Matrix.scale(3) @ (1, 2)
    Point(x=3.0, y=6.0)
    """

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    @classmethod
    def translate(cls, tx: float, ty: float = 0.0) -> Matrix:
        return cls(1.0, 0.0, 0.0, 1.0, tx, ty)

    @classmethod
    def scale(cls, sx: float, sy: float | None = None) -> Matrix:
        return cls(sx, 0.0, 0.0, sx if sy is None else sy, 0.0, 0.0)

    @classmethod
    def rotate(cls, angle: float, cx: float = 0.0, cy: float = 0.0) -> Matrix:
        rad = math.radians(angle)
        cos, sin = math.cos(rad), math.sin(rad)
        rotation = cls(cos, sin, -sin, cos, 0.0, 0.0)
        if cx or cy:
            return cls.translate(cx, cy) @ rotation @ cls.translate(-cx, -cy)
        return rotation

    @classmethod
    def flip_x(cls, x: float = 0.0) -> Matrix:
        """Mirror across the vertical line through *x*."""
        return cls(-1.0, 0.0, 0.0, 1.0, 2.0 * x, 0.0)

    @classmethod
    def flip_y(cls, y: float = 0.0) -> Matrix:
        """Mirror across the horizontal line through *y*."""
        return cls(1.0, 0.0, 0.0, -1.0, 0.0, 2.0 * y)

    @classmethod
    def skew_x(cls, angle: float) -> Matrix:
        return cls(1.0, 0.0, math.tan(math.radians(angle)), 1.0, 0.0, 0.0)

    @classmethod
    def skew_y(cls, angle: float) -> Matrix:
        return cls(1.0, math.tan(math.radians(angle)), 0.0, 1.0, 0.0, 0.0)

    @overload
    def __matmul__(self, other: Matrix) -> Matrix: ...
    @overload
    def __matmul__(self, other: Point | tuple[float, float]) -> Point: ...
    @overload
    def __matmul__(self, other: np.ndarray) -> np.ndarray: ...
    def __matmul__(self, other: Matrix | Point | tuple[float, float] | np.ndarray) -> Matrix | Point | np.ndarray:
        if isinstance(other, np.ndarray):
            return self.apply_points(other)
        if isinstance(other, tuple):
            return self.apply(*other)
        if not isinstance(other, Matrix):
            return NotImplemented
        return Matrix(
            self.a * other.a + self.c * other.b,
            self.b * other.a + self.d * other.b,
            self.a * other.c + self.c * other.d,
            self.b * other.c + self.d * other.d,
            self.a * other.e + self.c * other.f + self.e,
            self.b * other.e + self.d * other.f + self.f,
        )

    @property
    def determinant(self) -> float:
        return self.a * self.d - self.b * self.c

    @property
    def is_identity(self) -> bool:
        return self.isclose(IDENTITY)

    def inverse(self) -> Matrix:
        det = self.determinant
        if abs(det) < EPSILON:
            raise ValueError("matrix is not invertible")
        return Matrix(
            self.d / det,
            -self.b / det,
            -self.c / det,
            self.a / det,
            (self.c * self.f - self.d * self.e) / det,
            (self.b * self.e - self.a * self.f) / det,
        )

    def apply(self, x: float, y: float) -> Point:
        return Point(self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    def apply_points(self, points: np.ndarray) -> np.ndarray:
        """Map an ``(..., 2)`` array of points in one vectorized step.

        Examples
        --------
        >>> import numpy as np
        >>> Matrix.translate(1, 2) @ np.array([[0, 0], [1, 1]])
        array([[1., 2.],
               [2., 3.]])
        """
        array = np.asarray(points, dtype=float)
        if array.shape[-1:] != (2,):
            raise ValueError(f"points must have a last axis of length 2, got shape {array.shape}")
        return array @ np.array([[self.a, self.b], [self.c, self.d]]) + np.array([self.e, self.f])

    def __array__(self, dtype: object = None, copy: object = None) -> np.ndarray:
        """The 3x3 homogeneous matrix."""
        return np.array([[self.a, self.c, self.e], [self.b, self.d, self.f], [0.0, 0.0, 1.0]], dtype=dtype)

    @classmethod
    def from_array(cls, array: object) -> Matrix:
        """Build from a 3x3 (or 2x3) array in ``[[a, c, e], [b, d, f]]`` layout."""
        m = np.asarray(array, dtype=float)
        if m.shape not in ((3, 3), (2, 3)):
            raise ValueError(f"expected a 2x3 or 3x3 array, got shape {m.shape}")
        return cls(m[0, 0], m[1, 0], m[0, 1], m[1, 1], m[0, 2], m[1, 2])

    def as_tuple(self) -> Matrix6:
        return (self.a, self.b, self.c, self.d, self.e, self.f)

    def isclose(self, other: Matrix | object, tolerance: float = 1e-9) -> bool:
        """Equal within *tolerance*; *other* may be a matrix, ``Transform`` or transform text.

        Examples
        --------
        >>> Matrix.rotate(90).isclose("rotate(90)")
        True
        """
        if not isinstance(other, Matrix):
            from .transform import as_transform

            other = as_transform(other).to_matrix()  # type: ignore[arg-type]
        return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(self.as_tuple(), other.as_tuple(), strict=False))

    def decompose(self) -> tuple[float, float, float, float, float, float]:
        """``(tx, ty, angle, skew_x, sx, sy)`` with ``M = translate rotate skewX scale``.

        Angles are in degrees.
        """
        angle = math.atan2(self.b, self.a)
        cos, sin = math.cos(angle), math.sin(angle)
        sx = math.hypot(self.a, self.b)
        shear = cos * self.c + sin * self.d
        sy = -sin * self.c + cos * self.d
        skew = math.degrees(math.atan(shear / sy)) if sy else 0.0
        return (self.e, self.f, math.degrees(angle), skew, sx, sy)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """The shortest ``transform`` text for this matrix.

        Rigid motions become ``rotate(a cx cy)``; otherwise the parts of
        ``translate rotate skewX scale`` that are not identity, falling back
        to ``matrix(...)`` when that is shorter.

        Examples
        --------
        >>> Matrix.rotate(90, 5, 5).svg_value()
        'rotate(90 5 5)'
        >>> (Matrix.translate(10, 5) @ Matrix.scale(2, 3)).svg_value()
        'matrix(2 0 0 3 10 5)'
        >>> Matrix.skew_x(30).svg_value()
        'skewX(30)'
        """
        def num(value: float) -> str:
            return format_number(value, precision)

        def zero(value: float) -> bool:
            return num(value) in ("0", "-0")

        tx, ty, angle, skew, sx, sy = self.decompose()
        if zero(sx - 1) and zero(sy - 1) and zero(skew) and not zero(angle):
            rotation = Matrix.rotate(angle)
            denominator = (1 - rotation.a) ** 2 + rotation.b ** 2
            cx = ((1 - rotation.a) * tx - rotation.b * ty) / denominator
            cy = (rotation.b * tx + (1 - rotation.a) * ty) / denominator
            centre = "" if zero(cx) and zero(cy) else f" {num(cx)} {num(cy)}"
            return f"rotate({num(angle)}{centre})"
        parts = []
        if not (zero(tx) and zero(ty)):
            parts.append(f"translate({num(tx)})" if zero(ty) else f"translate({num(tx)} {num(ty)})")
        if not zero(angle):
            parts.append(f"rotate({num(angle)})")
        if not zero(skew):
            parts.append(f"skewX({num(skew)})")
        if not (zero(sx - 1) and zero(sy - 1)):
            parts.append(f"scale({num(sx)})" if zero(sx - sy) else f"scale({num(sx)} {num(sy)})")
        text = " ".join(parts)
        full = "matrix({})".format(" ".join(num(v) for v in self.as_tuple()))
        return text if len(text) <= len(full) else full

    def __str__(self) -> str:
        return self.svg_value()


IDENTITY: Final = Matrix()
