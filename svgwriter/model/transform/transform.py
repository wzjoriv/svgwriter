"""
Transform lists: parsing, building and composition.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import overload

from ..._internal._constants import DEFAULT_PRECISION
from ._constants import ARITY, FUNCTION_RE, NUMBER_RE
from ._transform_builders import TransformBuilders
from .matrix import Matrix, Point
from .ops import MatrixOp, Rotate, Scale, SkewX, SkewY, TransformOp, Translate

__all__ = ["Transform", "TransformLike", "as_transform", "parse_transform"]


class Transform(TransformBuilders):
    """An ordered list of transform operations.

    Builder methods append and return ``self``; called on the class they
    start a new list. ``@`` concatenates in SVG order (the right operand is
    applied first) and also accepts single operations and matrices.

    Parameters
    ----------
    ops : iterable of TransformOp, optional
        Initial operations. Defaults to an empty list.

    See Also
    --------
    Matrix : A single affine matrix.
    parse_transform : Build from ``transform`` attribute text.

    Examples
    --------
    >>> from svgwriter.model.transform import Transform
    >>> str(Transform().translate(10, 20).rotate(45))
    'translate(10 20) rotate(45)'
    >>> str(Transform.rotate(30) @ Transform.scale(2))
    'rotate(30) scale(2)'
    >>> Transform.translate(5) @ (1, 1)
    Point(x=6.0, y=1.0)
    """

    __slots__ = ("_ops",)

    def __init__(self, ops: Iterable[TransformOp] = ()) -> None:
        self._ops: list[TransformOp] = list(ops)

    @classmethod
    def parse(cls, text: str) -> Transform:
        """Parse a ``transform`` attribute value.

        Parameters
        ----------
        text : str
            Transform text such as ``"translate(5) scale(2)"``.

        Returns
        -------
        Transform
            The parsed list.

        Raises
        ------
        ValueError
            If the text is not a valid transform list.

        See Also
        --------
        parse_transform : The equivalent function.

        Examples
        --------
        >>> from svgwriter.model.transform import Transform
        >>> str(Transform.parse("translate(5) scale(2)"))
        'translate(5) scale(2)'
        """
        return parse_transform(text)

    def to_matrix(self) -> Matrix:
        """Collapse the list into a single matrix.

        Returns
        -------
        Matrix
            The product of every operation, in SVG order.

        Examples
        --------
        >>> from svgwriter.model.transform import Transform
        >>> str(Transform().translate(10, 0).scale(2).to_matrix())
        'matrix(2 0 0 2 10 0)'
        """
        result = Matrix()
        for op in self._ops:
            result = result @ op.to_matrix()
        return result

    def apply(self, x: float, y: float) -> Point:
        """Map a single point through the whole list.

        Parameters
        ----------
        x, y : float
            Coordinates of the point.

        Returns
        -------
        Point
            The transformed point.

        Examples
        --------
        >>> from svgwriter.model.transform import Transform
        >>> Transform().translate(10, 0).scale(2).apply(1, 1)
        Point(x=12.0, y=2.0)
        """
        return self.to_matrix().apply(x, y)

    def simplified(self) -> Transform:
        """Return an equivalent single ``matrix(...)`` transform.

        Returns
        -------
        Transform
            A one-operation list with the same effect.

        Examples
        --------
        >>> from svgwriter.model.transform import Transform
        >>> str(Transform().translate(10, 0).scale(2).simplified())
        'matrix(2 0 0 2 10 0)'
        """
        return Transform([MatrixOp(self.to_matrix())])

    @overload
    def __matmul__(self, other: Transform | TransformOp | Matrix) -> Transform: ...
    @overload
    def __matmul__(self, other: Point | tuple[float, float]) -> Point: ...
    def __matmul__(self, other: Transform | TransformOp | Matrix | Point | tuple[float, float]) -> Transform | Point:
        if isinstance(other, tuple):
            return self.apply(*other)
        if isinstance(other, (Transform, TransformOp, Matrix)):
            return Transform([*self._ops, *as_transform(other)._ops])
        return NotImplemented

    def __rmatmul__(self, other: TransformOp | Matrix) -> Transform:
        if isinstance(other, (TransformOp, Matrix)):
            return Transform([*as_transform(other)._ops, *self._ops])
        return NotImplemented

    def __imatmul__(self, other: Transform | TransformOp | Matrix) -> Transform:
        if not isinstance(other, (Transform, TransformOp, Matrix)):
            return NotImplemented
        self._ops.extend(as_transform(other)._ops)
        return self

    def inverse(self) -> Transform:
        """Return the inverse as a single ``matrix(...)``.

        Returns
        -------
        Transform
            A one-operation list that undoes this one.

        Raises
        ------
        ValueError
            If the transform is singular.

        Examples
        --------
        >>> from svgwriter.model.transform import Transform
        >>> str(Transform().translate(5, 0).inverse())
        'matrix(1 0 0 1 -5 0)'
        """
        return Transform([MatrixOp(self.to_matrix().inverse())])

    def __iter__(self) -> Iterator[TransformOp]:
        return iter(self._ops)

    def __len__(self) -> int:
        return len(self._ops)

    @overload
    def __getitem__(self, index: int) -> TransformOp: ...
    @overload
    def __getitem__(self, index: slice) -> Transform: ...
    def __getitem__(self, index: int | slice) -> TransformOp | Transform:
        if isinstance(index, slice):
            return Transform(self._ops[index])
        return self._ops[index]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Transform) and self._ops == other._ops

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Transform({self})"

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize the list as ``transform`` attribute text.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.

        Returns
        -------
        str
            Space-separated operations; empty for an empty list.

        Examples
        --------
        >>> from svgwriter.model.transform import Transform
        >>> Transform().translate(1.23456, 0).rotate(45).svg_value(2)
        'translate(1.23) rotate(45)'
        """
        return " ".join(op.svg_value(precision) for op in self._ops)

    def __str__(self) -> str:
        return self.svg_value()


TransformLike = Transform | TransformOp | Matrix | str


def _make_op(name: str, args: list[float]) -> TransformOp:
    if name == "matrix":
        return MatrixOp(Matrix(*args))
    if name == "translate":
        return Translate(*args)
    if name == "scale":
        return Scale(*args)
    if name == "rotate":
        return Rotate(*args)
    return SkewX(*args) if name == "skewX" else SkewY(*args)


def parse_transform(text: str) -> Transform:
    """Parse a ``transform`` attribute value.

    Parameters
    ----------
    text : str
        Transform text such as ``"rotate(45) translate(1 2)"``; separators may be spaces or commas.

    Returns
    -------
    Transform
        The parsed list of operations.

    Raises
    ------
    ValueError
        If the text contains anything other than valid transform functions,
        or a function has the wrong number of arguments.

    See Also
    --------
    as_transform : Also accepts matrices and single operations.

    Examples
    --------
    >>> from svgwriter.model.transform import parse_transform
    >>> str(parse_transform("rotate(45, 1, 2) skewX(3)"))
    'rotate(45 1 2) skewX(3)'
    """
    ops = []
    position = 0
    for match in FUNCTION_RE.finditer(text):
        if text[position:match.start()].strip(" \t\r\n,"):
            raise ValueError(f"invalid transform: {text!r}")
        position = match.end()
        name, body = match.groups()
        args = [float(n) for n in NUMBER_RE.findall(body)]
        if len(args) not in ARITY[name]:
            expected = " or ".join(str(n) for n in ARITY[name])
            raise ValueError(f"{name}() takes {expected} arguments, got {len(args)}: {text!r}")
        ops.append(_make_op(name, args))
    if text[position:].strip(" \t\r\n,"):
        raise ValueError(f"invalid transform: {text!r}")
    return Transform(ops)


def as_transform(value: TransformLike) -> Transform:
    """Coerce a transform-like value into a `Transform`.

    Parameters
    ----------
    value : Transform or TransformOp or Matrix or str
        The value to convert; text is parsed.

    Returns
    -------
    Transform
        `value` itself if it is already a `Transform`, otherwise a new list.

    Raises
    ------
    ValueError
        If `value` is text that is not a valid transform list.

    See Also
    --------
    parse_transform : Parse text only.

    Examples
    --------
    >>> from svgwriter.model.transform import Matrix, as_transform
    >>> str(as_transform("scale(2)"))
    'scale(2)'
    >>> str(as_transform(Matrix.scale(2)))
    'matrix(2 0 0 2 0 0)'
    """
    if isinstance(value, Transform):
        return value
    if isinstance(value, TransformOp):
        return Transform([value])
    if isinstance(value, Matrix):
        return Transform([MatrixOp(value)])
    return parse_transform(value)
