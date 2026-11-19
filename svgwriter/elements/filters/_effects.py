"""
Pixel-effect primitives: color matrix, convolution, blur, morphology, displacement and turbulence.
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from typing import Any, Final

from ..._internal._typing import Self
from .base import FilterPrimitive, SingleInput, TwoInputs

__all__ = [
    "Channel",
    "ColorMatrixType",
    "EdgeMode",
    "FeColorMatrix",
    "FeConvolveMatrix",
    "FeDisplacementMap",
    "FeGaussianBlur",
    "FeMorphology",
    "FeTurbulence",
    "MorphologyOperator",
    "TurbulenceType",
]

COLOR_MATRIX_SIZE: Final = 20
LUMA_RED: Final = 0.2126
LUMA_GREEN: Final = 0.7152
LUMA_BLUE: Final = 0.0722


class ColorMatrixType(str, enum.Enum):
    """Types of :class:`FeColorMatrix`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.ColorMatrixType.HUE_ROTATE.value
    'hueRotate'
    """

    MATRIX = "matrix"
    SATURATE = "saturate"
    HUE_ROTATE = "hueRotate"
    LUMINANCE_TO_ALPHA = "luminanceToAlpha"


class EdgeMode(str, enum.Enum):
    """Edge handling of :class:`FeConvolveMatrix`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.EdgeMode.WRAP.value
    'wrap'
    """

    DUPLICATE = "duplicate"
    WRAP = "wrap"
    NONE = "none"


class Channel(str, enum.Enum):
    """Color channels selectable in :class:`FeDisplacementMap`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.Channel.RED.value
    'R'
    """

    R = "R"
    G = "G"
    B = "B"
    A = "A"
    RED = "R"
    GREEN = "G"
    BLUE = "B"
    ALPHA = "A"


class MorphologyOperator(str, enum.Enum):
    """Operators of :class:`FeMorphology`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.MorphologyOperator.DILATE.value
    'dilate'
    """

    ERODE = "erode"
    DILATE = "dilate"


class TurbulenceType(str, enum.Enum):
    """Noise types of :class:`FeTurbulence`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.TurbulenceType.FRACTAL_NOISE.value
    'fractalNoise'
    """

    FRACTAL_NOISE = "fractalNoise"
    TURBULENCE = "turbulence"


class FeColorMatrix(SingleInput, tag="feColorMatrix"):
    """``<feColorMatrix>``: a 5x4 color transform or a shorthand.

    Parameters
    ----------
    type : ColorMatrixType, optional
        Kind of transform. Defaults to ``ColorMatrixType.MATRIX``.
    values : sequence of float or float, optional
        The 20 matrix entries for ``matrix``, otherwise the single amount. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Raises
    ------
    ValueError
        If a ``matrix`` is given other than 20 values.

    See Also
    --------
    FeComponentTransfer : Per-channel remapping.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeColorMatrix.saturate(0))
    '<feColorMatrix type="saturate" values="0"/>'
    """

    def __init__(
        self,
        type: ColorMatrixType = ColorMatrixType.MATRIX,
        values: Sequence[float] | float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if type is ColorMatrixType.MATRIX and isinstance(values, (list, tuple)) and len(values) != COLOR_MATRIX_SIZE:
            raise ValueError(f"a color matrix needs {COLOR_MATRIX_SIZE} values")
        self.update(type=type, values=tuple(values) if isinstance(values, (list, tuple)) else values)

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


class FeConvolveMatrix(SingleInput, tag="feConvolveMatrix"):
    """``<feConvolveMatrix>``: apply a convolution kernel.

    Parameters
    ----------
    kernel_matrix : sequence of float, optional
        The kernel, row by row. Defaults to empty.
    order : int or tuple of int, optional
        Kernel size, or ``(columns, rows)``. Defaults to 3.
    divisor, bias : float, optional
        Normalisation divisor and added bias. Default to None.
    target_x, target_y : int, optional
        Kernel cell aligned with the output pixel. Default to None.
    edge_mode : EdgeMode, optional
        Handling of pixels beyond the edge. Defaults to None.
    kernel_unit_length : float or tuple of float, optional
        Kernel scale. Defaults to None.
    preserve_alpha : bool, optional
        Leave the alpha channel unconvolved. Defaults to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Raises
    ------
    ValueError
        If the kernel length does not match `order`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeConvolveMatrix([0, 1, 0, 1, -4, 1, 0, 1, 0], divisor=1))
    '<feConvolveMatrix order="3" kernelMatrix="0 1 0 1 -4 1 0 1 0" divisor="1"/>'
    """

    def __init__(
        self,
        kernel_matrix: Sequence[float] = (),
        order: int | tuple[int, int] = 3,
        *,
        divisor: float | None = None,
        bias: float | None = None,
        target_x: int | None = None,
        target_y: int | None = None,
        edge_mode: EdgeMode | None = None,
        kernel_unit_length: float | tuple[float, float] | None = None,
        preserve_alpha: bool | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        columns, rows = (order, order) if isinstance(order, int) else order
        if kernel_matrix and len(kernel_matrix) != columns * rows:
            raise ValueError(f"kernel needs {columns * rows} values, got {len(kernel_matrix)}")
        self.update(
            order=order,
            kernel_matrix=tuple(kernel_matrix) or None,
            divisor=divisor,
            bias=bias,
            target_x=target_x,
            target_y=target_y,
            edge_mode=edge_mode,
            kernel_unit_length=kernel_unit_length,
            preserve_alpha=preserve_alpha,
        )


class FeGaussianBlur(SingleInput, tag="feGaussianBlur"):
    """``<feGaussianBlur>``: blur the input with a Gaussian.

    Parameters
    ----------
    std_deviation : float or tuple of float, optional
        Blur radius, or ``(x, y)``. Defaults to 0.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeGaussianBlur(std_deviation=2))
    '<feGaussianBlur stdDeviation="2"/>'
    """

    def __init__(self, std_deviation: float | tuple[float, float] = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(std_deviation=std_deviation)


class FeMorphology(SingleInput, tag="feMorphology"):
    """``<feMorphology>``: erode (thin) or dilate (fatten) the input.

    Parameters
    ----------
    operator : MorphologyOperator, optional
        ``erode`` or ``dilate``. Defaults to ``MorphologyOperator.ERODE``.
    radius : float or tuple of float, optional
        Radius, or ``(x, y)``. Defaults to 0.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeMorphology(svg.MorphologyOperator.DILATE, 2))
    '<feMorphology operator="dilate" radius="2"/>'
    """

    def __init__(
        self,
        operator: MorphologyOperator = MorphologyOperator.ERODE,
        radius: float | tuple[float, float] = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(operator=operator, radius=radius)


class FeDisplacementMap(TwoInputs, tag="feDisplacementMap"):
    """``<feDisplacementMap>``: displace ``in`` by channels of ``in2``.

    Parameters
    ----------
    scale : float, optional
        Displacement scale. Defaults to 0.
    x_channel_selector, y_channel_selector : Channel, optional
        Channels of ``in2`` driving each axis. Default to ``Channel.A``.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeDisplacementMap(5, svg.Channel.R, svg.Channel.G))
    '<feDisplacementMap scale="5" xChannelSelector="R" yChannelSelector="G"/>'
    """

    def __init__(
        self,
        scale: float = 0,
        x_channel_selector: Channel = Channel.A,
        y_channel_selector: Channel = Channel.A,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(scale=scale, x_channel_selector=x_channel_selector, y_channel_selector=y_channel_selector)


class FeTurbulence(FilterPrimitive, tag="feTurbulence"):
    """``<feTurbulence>``: Perlin noise.

    Parameters
    ----------
    base_frequency : float or tuple of float, optional
        Noise frequency, or ``(x, y)``. Defaults to 0.
    num_octaves : int, optional
        Number of noise layers. Defaults to 1.
    seed : float, optional
        Random seed. Defaults to None.
    stitch_tiles : bool, optional
        Stitch tile edges seamlessly. Defaults to False.
    type : TurbulenceType, optional
        ``turbulence`` or ``fractalNoise``. Defaults to ``TurbulenceType.TURBULENCE``.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeTurbulence(0.05, 2, seed=1))
    '<feTurbulence baseFrequency="0.05" numOctaves="2" seed="1" type="turbulence"/>'
    """

    def __init__(
        self,
        base_frequency: float | tuple[float, float] = 0,
        num_octaves: int = 1,
        *,
        seed: float | None = None,
        stitch_tiles: bool = False,
        type: TurbulenceType = TurbulenceType.TURBULENCE,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(
            base_frequency=base_frequency,
            num_octaves=num_octaves,
            seed=seed,
            stitch_tiles="stitch" if stitch_tiles else None,
            type=type,
        )
