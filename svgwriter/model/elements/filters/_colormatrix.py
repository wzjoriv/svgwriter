"""
Shortcut constructors for ``<feColorMatrix>``: saturate, hue rotation, luminance-to-alpha and grayscale.
"""

from __future__ import annotations

from typing import Any

from ...._internal._typing import Self
from ._constants import LUMA_BLUE, LUMA_GREEN, LUMA_RED

__all__ = ["ColorMatrixShortcuts"]


class ColorMatrixShortcuts:
    """Common color matrices; mixed into :class:`~svgwriter.model.elements.filters.FeColorMatrix`."""

    __slots__ = ()

    @classmethod
    def saturate(cls, amount: float, **kwargs: Any) -> Self:
        """Create a saturation adjustment.

        Parameters
        ----------
        amount : float
            0 gives grayscale and 1 leaves colors unchanged.
        **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

        Returns
        -------
        FeColorMatrix
            The new primitive.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.FeColorMatrix.saturate(0.5))
        '<feColorMatrix type="saturate" values="0.5"/>'
        """
        from ._effects import ColorMatrixType

        return cls(ColorMatrixType.SATURATE, amount, **kwargs)

    @classmethod
    def hue_rotate(cls, degrees: float, **kwargs: Any) -> Self:
        """Create a hue rotation.

        Parameters
        ----------
        degrees : float
            Angle of the rotation around the hue circle.
        **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

        Returns
        -------
        FeColorMatrix
            The new primitive.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.FeColorMatrix.hue_rotate(90))
        '<feColorMatrix type="hueRotate" values="90"/>'
        """
        from ._effects import ColorMatrixType

        return cls(ColorMatrixType.HUE_ROTATE, degrees, **kwargs)

    @classmethod
    def luminance_to_alpha(cls, **kwargs: Any) -> Self:
        """Create a transform that moves luminance into the alpha channel.

        Parameters
        ----------
        **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

        Returns
        -------
        FeColorMatrix
            The new primitive.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.FeColorMatrix.luminance_to_alpha())
        '<feColorMatrix type="luminanceToAlpha"/>'
        """
        from ._effects import ColorMatrixType

        return cls(ColorMatrixType.LUMINANCE_TO_ALPHA, **kwargs)

    @classmethod
    def grayscale(cls, **kwargs: Any) -> Self:
        """Create a matrix converting colors to luminance gray, keeping alpha.

        Parameters
        ----------
        **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

        Returns
        -------
        FeColorMatrix
            The new primitive.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FeColorMatrix.grayscale().get("type").value
        'matrix'
        """
        row = (LUMA_RED, LUMA_GREEN, LUMA_BLUE, 0.0, 0.0)
        return cls(values=row * 3 + (0.0, 0.0, 0.0, 1.0, 0.0), **kwargs)
