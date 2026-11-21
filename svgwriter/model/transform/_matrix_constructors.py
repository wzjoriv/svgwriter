"""
Named constructors of a matrix: translation, scaling, rotation, flips and skews.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .matrix import Matrix

__all__ = ["MatrixConstructors"]


class MatrixConstructors:
    """Class-level constructors of :class:`~svgwriter.model.transform.Matrix`."""

    __slots__ = ()

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
        >>> from svgwriter.model.transform import Matrix
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
        >>> from svgwriter.model.transform import Matrix
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
        >>> from svgwriter.model.transform import Matrix
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
        >>> from svgwriter.model.transform import Matrix
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
        >>> from svgwriter.model.transform import Matrix
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
        >>> from svgwriter.model.transform import Matrix
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
        >>> from svgwriter.model.transform import Matrix
        >>> Matrix.skew_y(45).isclose(Matrix(1, 1, 0, 1, 0, 0))
        True
        """
        return cls(1.0, math.tan(math.radians(angle)), 0.0, 1.0, 0.0, 0.0)
