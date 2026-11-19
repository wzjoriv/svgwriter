"""
2-D affine matrices in SVG's ``[a b c d e f]`` layout.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final, NamedTuple, overload

import numpy as np

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number
from .._internal._typing import Matrix6

__all__ = ["IDENTITY", "Matrix", "Point"]

EPSILON: Final = 1e-12


class Point(NamedTuple):
    """A 2-D point that is also a vector.

    A named tuple, so it unpacks and compares as ``(x, y)``. Arithmetic is
    element-wise like numpy: ``+`` and ``-`` take another point or pair,
    ``*`` and ``/`` a number or pair; ``abs(p)`` is the length.

    Parameters
    ----------
    x, y : float
        Coordinates.

    Examples
    --------
    >>> from svgwriter.transform import Point
    >>> x, y = Point(1, 2)
    >>> Point(1, 2) == (1, 2)
    True
    >>> Point(1, 2) + (3, 4), Point(1, 2) * 2, -Point(1, 2)
    (Point(x=4.0, y=6.0), Point(x=2.0, y=4.0), Point(x=-1.0, y=-2.0))
    >>> abs(Point(3, 4))
    5.0
    """

    x: float
    y: float

    def __add__(self, other: object) -> Point:  # type: ignore[override]
        ox, oy = _pair(other)
        return Point(self.x + ox, self.y + oy)

    __radd__ = __add__

    def __sub__(self, other: object) -> Point:
        ox, oy = _pair(other)
        return Point(self.x - ox, self.y - oy)

    def __rsub__(self, other: object) -> Point:
        ox, oy = _pair(other)
        return Point(ox - self.x, oy - self.y)

    def __mul__(self, other: object) -> Point:  # type: ignore[override]
        ox, oy = _pair(other)
        return Point(self.x * ox, self.y * oy)

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> Point:
        ox, oy = _pair(other)
        return Point(self.x / ox, self.y / oy)

    def __neg__(self) -> Point:
        return Point(-float(self.x), -float(self.y))

    def __abs__(self) -> float:
        return math.hypot(self.x, self.y)

    def __array__(self, dtype: object = None, copy: object = None) -> Any:
        import numpy as np

        return np.array((self.x, self.y), dtype=dtype or float)


def _pair(value: object) -> tuple[float, float]:
    """A number broadcast to ``(v, v)`` or any two-item sequence, as floats."""
    if isinstance(value, (int, float)):
        return float(value), float(value)
    try:
        x, y = value  # type: ignore[misc]
        return float(x), float(y)
    except (TypeError, ValueError):
        raise TypeError(f"expected a number or an (x, y) pair, got {value!r}") from None


@dataclass(frozen=True, slots=True)
class Matrix:
    """An affine transform ``[a c e; b d f; 0 0 1]``.

    Matrices compose with ``@`` in SVG order: ``m1 @ m2`` applies ``m2``
    first, matching ``transform="m1 m2"``. Instances are immutable.

    Parameters
    ----------
    a, b, c, d, e, f : float, optional
        The six SVG matrix entries; ``e`` and ``f`` are the translation.
        Default to the identity (1, 0, 0, 1, 0, 0).

    See Also
    --------
    Transform : An ordered list of transform operations.

    Examples
    --------
    >>> from svgwriter.transform import Matrix
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
        """Return a translation.

        Parameters
        ----------
        tx : float
            Offset along x.
        ty : float, optional
            Offset along y. Defaults to 0.

        Returns
        -------
        Matrix
            The translation matrix.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.translate(3, 4).apply(1, 1)
        Point(x=4.0, y=5.0)
        """
        return cls(1.0, 0.0, 0.0, 1.0, tx, ty)

    @classmethod
    def scale(cls, sx: float, sy: float | None = None) -> Matrix:
        """Return a scaling about the origin.

        Parameters
        ----------
        sx : float
            Factor along x.
        sy : float, optional
            Factor along y. Defaults to `sx` (uniform scaling).

        Returns
        -------
        Matrix
            The scaling matrix.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.scale(2, 3).apply(1, 1)
        Point(x=2.0, y=3.0)
        """
        return cls(sx, 0.0, 0.0, sx if sy is None else sy, 0.0, 0.0)

    @classmethod
    def rotate(cls, angle: float, cx: float = 0.0, cy: float = 0.0) -> Matrix:
        """Return a rotation, optionally about a centre.

        Parameters
        ----------
        angle : float
            Angle in degrees; positive is clockwise in SVG's y-down coordinates.
        cx, cy : float, optional
            Centre of rotation. Default to the origin.

        Returns
        -------
        Matrix
            The rotation matrix.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> p = Matrix.rotate(90, 5, 5).apply(10, 5)
        >>> round(p.x, 6), round(p.y, 6)
        (5.0, 10.0)
        """
        rad = math.radians(angle)
        cos, sin = math.cos(rad), math.sin(rad)
        rotation = cls(cos, sin, -sin, cos, 0.0, 0.0)
        if cx or cy:
            return cls.translate(cx, cy) @ rotation @ cls.translate(-cx, -cy)
        return rotation

    @classmethod
    def flip_x(cls, x: float = 0.0) -> Matrix:
        """Return a mirror across a vertical line.

        Parameters
        ----------
        x : float, optional
            The x coordinate of the mirror line. Defaults to 0.

        Returns
        -------
        Matrix
            The reflection matrix.

        See Also
        --------
        flip_y : Mirror across a horizontal line.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.flip_x(5).apply(1, 1)
        Point(x=9.0, y=1.0)
        """
        return cls(-1.0, 0.0, 0.0, 1.0, 2.0 * x, 0.0)

    @classmethod
    def flip_y(cls, y: float = 0.0) -> Matrix:
        """Return a mirror across a horizontal line.

        Parameters
        ----------
        y : float, optional
            The y coordinate of the mirror line. Defaults to 0.

        Returns
        -------
        Matrix
            The reflection matrix.

        See Also
        --------
        flip_x : Mirror across a vertical line.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.flip_y(5).apply(1, 1)
        Point(x=1.0, y=9.0)
        """
        return cls(1.0, 0.0, 0.0, -1.0, 0.0, 2.0 * y)

    @classmethod
    def skew_x(cls, angle: float) -> Matrix:
        """Return a horizontal skew.

        Parameters
        ----------
        angle : float
            Skew angle in degrees along the x axis.

        Returns
        -------
        Matrix
            The skew matrix.

        See Also
        --------
        skew_y : Vertical skew.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> str(Matrix.skew_x(30))
        'skewX(30)'
        """
        return cls(1.0, 0.0, math.tan(math.radians(angle)), 1.0, 0.0, 0.0)

    @classmethod
    def skew_y(cls, angle: float) -> Matrix:
        """Return a vertical skew.

        Parameters
        ----------
        angle : float
            Skew angle in degrees along the y axis.

        Returns
        -------
        Matrix
            The skew matrix.

        See Also
        --------
        skew_x : Horizontal skew.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.skew_y(45).isclose(Matrix(1, 1, 0, 1, 0, 0))
        True
        """
        return cls(1.0, math.tan(math.radians(angle)), 0.0, 1.0, 0.0, 0.0)

    @overload
    def __matmul__(self, other: Matrix) -> Matrix: ...
    @overload
    def __matmul__(self, other: Point | tuple[float, float]) -> Point: ...
    @overload
    def __matmul__(self, other: np.ndarray) -> np.ndarray: ...
    def __matmul__(self, other: Matrix | Point | tuple[float, float] | np.ndarray) -> Matrix | Point | np.ndarray:
        """Compose with a matrix, or map a point or an array of points."""
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
        """The determinant ``a*d - b*c``; negative when the transform mirrors.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.scale(2, 3).determinant
        6.0
        """
        return self.a * self.d - self.b * self.c

    @property
    def is_identity(self) -> bool:
        """Whether the matrix equals the identity within tolerance.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix().is_identity
        True
        >>> Matrix.translate(1).is_identity
        False
        """
        return self.isclose(IDENTITY)

    def inverse(self) -> Matrix:
        """Return the inverse transform.

        Returns
        -------
        Matrix
            The matrix that undoes this one.

        Raises
        ------
        ValueError
            If the matrix is singular.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> str(Matrix.translate(5, 0).inverse())
        'translate(-5)'
        """
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
        """Map a single point.

        Parameters
        ----------
        x, y : float
            Coordinates of the point.

        Returns
        -------
        Point
            The transformed point.

        See Also
        --------
        apply_points : Vectorized version.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.translate(1, 2).apply(1, 1)
        Point(x=2.0, y=3.0)
        """
        return Point(self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    def apply_points(self, points: np.ndarray) -> np.ndarray:
        """Map an ``(..., 2)`` array of points in one vectorized step.

        Parameters
        ----------
        points : numpy.ndarray
            Array whose last axis holds ``x, y`` pairs.

        Returns
        -------
        numpy.ndarray
            Float array of the same shape with every point mapped.

        Raises
        ------
        ValueError
            If the last axis does not have length 2.

        See Also
        --------
        apply : Map a single point.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.transform import Matrix
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
        """Build a matrix from a 3x3 (or 2x3) array.

        Parameters
        ----------
        array : array_like
            Array in ``[[a, c, e], [b, d, f]]`` layout; a third row is ignored.

        Returns
        -------
        Matrix
            The matrix with those entries.

        Raises
        ------
        ValueError
            If the array is not 2x3 or 3x3.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> str(Matrix.from_array([[1, 0, 5], [0, 1, 6]]))
        'translate(5 6)'
        """
        m = np.asarray(array, dtype=float)
        if m.shape not in ((3, 3), (2, 3)):
            raise ValueError(f"expected a 2x3 or 3x3 array, got shape {m.shape}")
        return cls(m[0, 0], m[1, 0], m[0, 1], m[1, 1], m[0, 2], m[1, 2])

    def as_tuple(self) -> Matrix6:
        """Return the entries as ``(a, b, c, d, e, f)``.

        Returns
        -------
        tuple of float
            The six matrix entries in SVG ``matrix()`` order.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.translate(5, 6).as_tuple()
        (1.0, 0.0, 0.0, 1.0, 5, 6)
        """
        return (self.a, self.b, self.c, self.d, self.e, self.f)

    def isclose(self, other: Matrix | object, tolerance: float = 1e-9) -> bool:
        """Return whether another transform is equal within a tolerance.

        Parameters
        ----------
        other : Matrix or Transform or str
            What to compare with; a `Transform` or transform text is converted to a matrix.
        tolerance : float, optional
            Largest allowed difference between corresponding entries. Defaults to 1e-9.

        Returns
        -------
        bool
            True if every entry is within `tolerance`.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> Matrix.rotate(90).isclose("rotate(90)")
        True
        """
        if not isinstance(other, Matrix):
            from .transform import as_transform

            other = as_transform(other).to_matrix()  # type: ignore[arg-type]
        return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(self.as_tuple(), other.as_tuple(), strict=False))

    def decompose(self) -> tuple[float, float, float, float, float, float]:
        """Decompose into translation, rotation, skew and scale.

        The parts satisfy ``M = translate rotate skewX scale``.

        Returns
        -------
        tuple of float
            ``(tx, ty, angle, skew_x, sx, sy)``; angles are in degrees.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
        >>> (Matrix.translate(10, 5) @ Matrix.scale(2)).decompose()
        (10.0, 5.0, 0.0, 0.0, 2.0, 2.0)
        """
        angle = math.atan2(self.b, self.a)
        cos, sin = math.cos(angle), math.sin(angle)
        sx = math.hypot(self.a, self.b)
        shear = cos * self.c + sin * self.d
        sy = -sin * self.c + cos * self.d
        skew = math.degrees(math.atan(shear / sy)) if sy else 0.0
        return (self.e, self.f, math.degrees(angle), skew, sx, sy)

    def svg_value(self, precision: int = DEFAULT_PRECISION, *, pivot: tuple[float, float] | None = None,
                  box: Any = None) -> str:
        """The shortest ``transform`` text for this matrix.

        Rigid motions become ``rotate(a cx cy)``; otherwise the parts of
        ``translate rotate skewX scale`` that are not identity, falling back
        to ``matrix(...)`` when that is shorter.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.
        pivot : (float, float), optional
            The element's own pivot (its anchor). When a pure rotation's
            centre would fall outside *box*, the text becomes
            ``translate(dx dy) rotate(a px py)`` about this point instead,
            which is what a person would write. Defaults to None.
        box : BBox, optional
            The element's local bounding box, used with *pivot*. Defaults to None.

        Returns
        -------
        str
            Text suitable for a ``transform`` attribute; empty for the identity.

        Examples
        --------
        >>> from svgwriter.transform import Matrix
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
            if pivot is not None and box is not None and not _inside(box, cx, cy):
                px, py = float(pivot[0]), float(pivot[1])
                moved = self.apply(px, py)
                dx, dy = moved.x - px, moved.y - py
                shift = "" if zero(dx) and zero(dy) else (
                    f"translate({num(dx)}) " if zero(dy) else f"translate({num(dx)} {num(dy)}) ")
                return f"{shift}rotate({num(angle)} {num(px)} {num(py)})"
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


def _inside(box: Any, x: float, y: float) -> bool:
    """Whether ``(x, y)`` lies within the box (edges included)."""
    return box.x <= x <= box.x + box.width and box.y <= y <= box.y + box.height


IDENTITY: Final = Matrix()
