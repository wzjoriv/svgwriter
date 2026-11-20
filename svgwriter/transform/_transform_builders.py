"""
Chainable operations appended to a transform list.
"""

from __future__ import annotations

from .._internal._hybrid import hybridmethod
from .matrix import Matrix
from .ops import MatrixOp, Rotate, Scale, SkewX, SkewY, TransformOp, Translate

__all__ = ["TransformBuilders"]


class TransformBuilders:
    """``translate``, ``scale``, ``rotate``, skews and ``matrix`` of :class:`~svgwriter.transform.Transform`."""

    __slots__ = ()

    _ops: list[TransformOp]

    @hybridmethod
    def translate(self, tx: float, ty: float = 0.0) -> None:
        """Append a translation.

        Parameters
        ----------
        tx : float
            Offset along x.
        ty : float, optional
            Offset along y. Defaults to 0.

        Returns
        -------
        Transform
            This list (or a new one when called on the class), for chaining.

        Examples
        --------
        >>> from svgwriter.transform import Transform
        >>> str(Transform.translate(10, 5))
        'translate(10 5)'
        """
        self._ops.append(Translate(tx, ty))

    @hybridmethod
    def scale(self, sx: float, sy: float | None = None) -> None:
        """Append a scaling.

        Parameters
        ----------
        sx : float
            Factor along x.
        sy : float, optional
            Factor along y. Defaults to `sx`.

        Returns
        -------
        Transform
            This list (or a new one when called on the class), for chaining.

        Examples
        --------
        >>> from svgwriter.transform import Transform
        >>> str(Transform().scale(2, 3))
        'scale(2 3)'
        """
        self._ops.append(Scale(sx, sy))

    @hybridmethod
    def rotate(self, angle: float, cx: float = 0.0, cy: float = 0.0) -> None:
        """Append a rotation.

        Parameters
        ----------
        angle : float
            Angle in degrees; positive is clockwise.
        cx, cy : float, optional
            Centre of rotation. Default to the origin.

        Returns
        -------
        Transform
            This list (or a new one when called on the class), for chaining.

        Examples
        --------
        >>> from svgwriter.transform import Transform
        >>> str(Transform.rotate(45, 5, 5))
        'rotate(45 5 5)'
        """
        self._ops.append(Rotate(angle, cx, cy))

    @hybridmethod
    def skew_x(self, angle: float) -> None:
        """Append a horizontal skew.

        Parameters
        ----------
        angle : float
            Skew angle in degrees.

        Returns
        -------
        Transform
            This list (or a new one when called on the class), for chaining.

        Examples
        --------
        >>> from svgwriter.transform import Transform
        >>> str(Transform.skew_x(30))
        'skewX(30)'
        """
        self._ops.append(SkewX(angle))

    @hybridmethod
    def skew_y(self, angle: float) -> None:
        """Append a vertical skew.

        Parameters
        ----------
        angle : float
            Skew angle in degrees.

        Returns
        -------
        Transform
            This list (or a new one when called on the class), for chaining.

        Examples
        --------
        >>> from svgwriter.transform import Transform
        >>> str(Transform.skew_y(30))
        'skewY(30)'
        """
        self._ops.append(SkewY(angle))

    @hybridmethod
    def matrix(self, a: float, b: float, c: float, d: float, e: float, f: float) -> None:
        """Append a literal matrix.

        Parameters
        ----------
        a, b, c, d, e, f : float
            The six SVG matrix entries.

        Returns
        -------
        Transform
            This list (or a new one when called on the class), for chaining.

        Examples
        --------
        >>> from svgwriter.transform import Transform
        >>> str(Transform.matrix(1, 0, 0, 1, 5, 6))
        'matrix(1 0 0 1 5 6)'
        """
        self._ops.append(MatrixOp(Matrix(a, b, c, d, e, f)))
