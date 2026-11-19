"""``feComponentTransfer`` and its ``feFuncR/G/B/A`` children."""

from __future__ import annotations

import enum
from collections.abc import Sequence
from typing import Any

from ..._internal._typing import Self
from .._mixins import CoreAttributes
from ..base import ContentModel
from ..container import Container
from .base import SingleInput

__all__ = ["FeComponentTransfer", "FeFunc", "FeFuncA", "FeFuncB", "FeFuncG", "FeFuncR", "TransferType"]


def _numbers(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    return [float(v) for v in str(value).replace(",", " ").split()]


class TransferType(str, enum.Enum):
    """Transfer function types of :class:`FeFunc`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.TransferType.GAMMA.value
    'gamma'
    """

    IDENTITY = "identity"
    TABLE = "table"
    DISCRETE = "discrete"
    LINEAR = "linear"
    GAMMA = "gamma"


class FeFunc(CoreAttributes, content=ContentModel.ELEMENTS):
    """Shared base of the four channel transfer functions.

    Parameters
    ----------
    type : TransferType, optional
        Kind of function. Defaults to ``TransferType.IDENTITY``.
    table_values : sequence of float, optional
        Lookup table for ``table`` and ``discrete``. Defaults to None.
    slope, intercept : float, optional
        Coefficients of ``linear``. Default to None.
    amplitude, exponent, offset : float, optional
        Coefficients of ``gamma``. Default to None.
    **kwargs
        Core and other SVG attributes in Python spelling.

    See Also
    --------
    FeComponentTransfer : The primitive that holds these functions.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeFuncR.linear(2, 0.1))
    '<feFuncR type="linear" slope="2" intercept="0.1"/>'
    """

    def __init__(
        self,
        type: TransferType = TransferType.IDENTITY,
        *,
        table_values: Sequence[float] | None = None,
        slope: float | None = None,
        intercept: float | None = None,
        amplitude: float | None = None,
        exponent: float | None = None,
        offset: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.update(
            type=type,
            table_values=tuple(table_values) if table_values is not None else None,
            slope=slope,
            intercept=intercept,
            amplitude=amplitude,
            exponent=exponent,
            offset=offset,
        )

    @classmethod
    def linear(cls, slope: float, intercept: float = 0, **kwargs: Any) -> Self:
        """Create a linear transfer function, ``slope * C + intercept``.

        Parameters
        ----------
        slope : float
            Multiplier.
        intercept : float, optional
            Added constant. Defaults to 0.
        **kwargs
            Core and other SVG attributes in Python spelling.

        Returns
        -------
        FeFunc
            The new function element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.FeFuncA.linear(0.5))
        '<feFuncA type="linear" slope="0.5" intercept="0"/>'
        """
        return cls(TransferType.LINEAR, slope=slope, intercept=intercept, **kwargs)

    @classmethod
    def table(cls, *values: float, **kwargs: Any) -> Self:
        """Create a piecewise-linear transfer function from lookup values.

        Parameters
        ----------
        *values : float
            Table entries, evenly spaced over the input range.
        **kwargs
            Core and other SVG attributes in Python spelling.

        Returns
        -------
        FeFunc
            The new function element.

        See Also
        --------
        evaluate : Apply the function to a value.

        Examples
        --------
        >>> import svgwriter as svg
        >>> str(svg.FeFuncR.table(0, 1))
        '<feFuncR type="table" tableValues="0 1"/>'
        """
        return cls(TransferType.TABLE, table_values=values, **kwargs)

    @classmethod
    def gamma(cls, amplitude: float = 1, exponent: float = 1, offset: float = 0, **kwargs: Any) -> Self:
        """Create a gamma transfer function, ``amplitude * C ** exponent + offset``.

        Parameters
        ----------
        amplitude : float, optional
            Multiplier. Defaults to 1.
        exponent : float, optional
            Power applied to the channel. Defaults to 1.
        offset : float, optional
            Added constant. Defaults to 0.
        **kwargs
            Core and other SVG attributes in Python spelling.

        Returns
        -------
        FeFunc
            The new function element.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FeFuncG.gamma(2, 3).evaluate(0.5)
        0.25
        """
        return cls(TransferType.GAMMA, amplitude=amplitude, exponent=exponent, offset=offset, **kwargs)

    def evaluate(self, c: float) -> float:
        """Apply this transfer function to a channel value.

        Parameters
        ----------
        c : float
            Channel value in ``0..1``.

        Returns
        -------
        float
            The transformed value.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FeFuncR.linear(2, 0.1).evaluate(0.5)
        1.1
        """
        kind = TransferType(self.get("type", TransferType.IDENTITY))
        table = _numbers(self.get("tableValues"))
        if kind is TransferType.LINEAR:
            return float(self.get("slope", 1)) * c + float(self.get("intercept", 0))
        if kind is TransferType.GAMMA:
            return float(self.get("amplitude", 1)) * c ** float(self.get("exponent", 1)) + float(self.get("offset", 0))
        if kind is TransferType.TABLE and len(table) > 1:
            n = len(table) - 1
            k = min(int(c * n), n - 1)
            return table[k] + (c * n - k) * (table[k + 1] - table[k])
        if kind is TransferType.DISCRETE and table:
            return table[min(int(c * len(table)), len(table) - 1)]
        return c


class FeFuncR(FeFunc, tag="feFuncR"):
    """``<feFuncR>``: the transfer function of the red channel.

    Takes the parameters of :class:`FeFunc`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeFuncR.table(0, 1))
    '<feFuncR type="table" tableValues="0 1"/>'
    """


class FeFuncG(FeFunc, tag="feFuncG"):
    """``<feFuncG>``: the transfer function of the green channel.

    Takes the parameters of :class:`FeFunc`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.FeFuncG.tag
    'feFuncG'
    """


class FeFuncB(FeFunc, tag="feFuncB"):
    """``<feFuncB>``: the transfer function of the blue channel.

    Takes the parameters of :class:`FeFunc`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.FeFuncB.tag
    'feFuncB'
    """


class FeFuncA(FeFunc, tag="feFuncA"):
    """``<feFuncA>``: the transfer function of the alpha channel.

    Takes the parameters of :class:`FeFunc`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.FeFuncA.tag
    'feFuncA'
    """


class FeComponentTransfer(SingleInput, Container[FeFunc], tag="feComponentTransfer"):
    """``<feComponentTransfer>``: per-channel remapping.

    Parameters
    ----------
    *functions : FeFunc
        Channel functions to add as children.
    red, green, blue, alpha : FeFunc, optional
        Functions for one channel each; they are converted to the matching
        ``feFuncR``/``G``/``B``/``A`` element. Default to None.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), ``result``, ``in_``
        and other SVG attributes in Python spelling.

    See Also
    --------
    FeColorMatrix : Mix channels with a matrix.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeComponentTransfer(red=svg.FeFuncR.linear(2)))
    '<feComponentTransfer><feFuncR type="linear" slope="2" intercept="0"/></feComponentTransfer>'
    """

    def __init__(
        self,
        *functions: FeFunc,
        red: FeFunc | None = None,
        green: FeFunc | None = None,
        blue: FeFunc | None = None,
        alpha: FeFunc | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*functions, **kwargs)
        for func, cls in ((red, FeFuncR), (green, FeFuncG), (blue, FeFuncB), (alpha, FeFuncA)):
            if func is not None:
                self.add(func if isinstance(func, cls) else cls.from_attributes(func.attributes))
