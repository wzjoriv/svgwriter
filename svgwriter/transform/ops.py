"""The six SVG transform functions as value objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number
from .matrix import Matrix

__all__ = ["MatrixOp", "Rotate", "Scale", "SkewX", "SkewY", "TransformOp", "Translate"]


class TransformOp(ABC):
    """One entry of a ``transform`` list.

    Base class of the six SVG transform functions. Each operation knows its
    keyword and arguments and can be turned into a `Matrix`.

    Attributes
    ----------
    keyword : str
        The SVG function name, such as ``"translate"``.

    See Also
    --------
    Transform : A list of operations.

    Examples
    --------
    >>> from svgwriter.transform import Translate
    >>> isinstance(Translate(1), TransformOp)
    True
    """

    keyword: ClassVar[str]

    @property
    @abstractmethod
    def arguments(self) -> tuple[float, ...]:
        """The numbers written inside the parentheses.

        Examples
        --------
        >>> from svgwriter.transform import Translate
        >>> Translate(1, 2).arguments
        (1, 2)
        """

    @abstractmethod
    def to_matrix(self) -> Matrix:
        """Return the matrix equivalent of this operation.

        Returns
        -------
        Matrix
            The operation as an affine matrix.

        Examples
        --------
        >>> from svgwriter.transform import Translate
        >>> str(Translate(1, 2).to_matrix())
        'translate(1 2)'
        """

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the operation as transform text.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.

        Returns
        -------
        str
            The keyword with its arguments, such as ``"rotate(45)"``.

        Examples
        --------
        >>> from svgwriter.transform import Scale
        >>> Scale(1.23456).svg_value(2)
        'scale(1.23)'
        """
        args = " ".join(format_number(a, precision) for a in self.arguments)
        return f"{self.keyword}({args})"

    def __str__(self) -> str:
        return self.svg_value()


@dataclass(frozen=True)
class Translate(TransformOp):
    """Move by an offset (``translate``).

    A frozen dataclass; a zero `ty` is omitted when serialized.

    Parameters
    ----------
    tx : float
        Offset along x.
    ty : float, optional
        Offset along y. Defaults to 0.

    See Also
    --------
    Matrix.translate : The equivalent matrix.

    Examples
    --------
    >>> from svgwriter.transform import Translate
    >>> str(Translate(10, 5))
    'translate(10 5)'
    """

    keyword: ClassVar[str] = "translate"
    tx: float
    ty: float = 0.0

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.tx,) if self.ty == 0 else (self.tx, self.ty)

    def to_matrix(self) -> Matrix:
        return Matrix.translate(self.tx, self.ty)


@dataclass(frozen=True)
class Scale(TransformOp):
    """Scale about the origin (``scale``).

    With no `sy` the scaling is uniform.

    Parameters
    ----------
    sx : float
        Factor along x.
    sy : float, optional
        Factor along y. Defaults to None, meaning `sx`.

    See Also
    --------
    Matrix.scale : The equivalent matrix.

    Examples
    --------
    >>> from svgwriter.transform import Scale
    >>> str(Scale(2))
    'scale(2)'
    """

    keyword: ClassVar[str] = "scale"
    sx: float
    sy: float | None = None

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.sx,) if self.sy is None else (self.sx, self.sy)

    def to_matrix(self) -> Matrix:
        return Matrix.scale(self.sx, self.sy)


@dataclass(frozen=True)
class Rotate(TransformOp):
    """Rotate by an angle, optionally about a centre (``rotate``).

    The centre is omitted when serialized if it is the origin.

    Parameters
    ----------
    angle : float
        Angle in degrees; positive is clockwise.
    cx, cy : float, optional
        Centre of rotation. Default to 0.

    See Also
    --------
    Matrix.rotate : The equivalent matrix.

    Examples
    --------
    >>> from svgwriter.transform import Rotate
    >>> str(Rotate(45, 5, 5))
    'rotate(45 5 5)'
    """

    keyword: ClassVar[str] = "rotate"
    angle: float
    cx: float = 0.0
    cy: float = 0.0

    @property
    def arguments(self) -> tuple[float, ...]:
        if self.cx == 0 and self.cy == 0:
            return (self.angle,)
        return (self.angle, self.cx, self.cy)

    def to_matrix(self) -> Matrix:
        return Matrix.rotate(self.angle, self.cx, self.cy)


@dataclass(frozen=True)
class SkewX(TransformOp):
    """Skew along the x axis (``skewX``).

    Shears horizontally by an angle.

    Parameters
    ----------
    angle : float
        Skew angle in degrees.

    See Also
    --------
    SkewY : The vertical counterpart.

    Examples
    --------
    >>> from svgwriter.transform import SkewX
    >>> str(SkewX(30))
    'skewX(30)'
    """

    keyword: ClassVar[str] = "skewX"
    angle: float

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.angle,)

    def to_matrix(self) -> Matrix:
        return Matrix.skew_x(self.angle)


@dataclass(frozen=True)
class SkewY(TransformOp):
    """Skew along the y axis (``skewY``).

    Shears vertically by an angle.

    Parameters
    ----------
    angle : float
        Skew angle in degrees.

    See Also
    --------
    SkewX : The horizontal counterpart.

    Examples
    --------
    >>> from svgwriter.transform import SkewY
    >>> str(SkewY(30))
    'skewY(30)'
    """

    keyword: ClassVar[str] = "skewY"
    angle: float

    @property
    def arguments(self) -> tuple[float, ...]:
        return (self.angle,)

    def to_matrix(self) -> Matrix:
        return Matrix.skew_y(self.angle)


@dataclass(frozen=True)
class MatrixOp(TransformOp):
    """A literal matrix (``matrix``).

    Wraps a `Matrix` so it can sit in a transform list.

    Parameters
    ----------
    matrix : Matrix
        The matrix to apply.

    See Also
    --------
    Matrix : The wrapped value.

    Examples
    --------
    >>> from svgwriter.transform import MatrixOp
    >>> from svgwriter.transform import Matrix
    >>> str(MatrixOp(Matrix.scale(2)))
    'matrix(2 0 0 2 0 0)'
    """

    keyword: ClassVar[str] = "matrix"
    matrix: Matrix

    @property
    def arguments(self) -> tuple[float, ...]:
        return self.matrix.as_tuple()

    def to_matrix(self) -> Matrix:
        return self.matrix
