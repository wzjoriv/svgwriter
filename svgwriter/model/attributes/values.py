"""
Attribute value serialization via ``functools.singledispatch``.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from functools import singledispatch

import numpy as np

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._numbers import format_number
from .protocols import SupportsSVG

__all__ = ["format_value"]


@singledispatch
def format_value(value: object, precision: int = DEFAULT_PRECISION) -> str:
    """Render a value as the text of an SVG attribute.

    Dispatches on type: strings pass through, booleans become ``true``/``false``,
    floats use the shortest form, sequences are space-separated (with ``x,y``
    pairs for nested ones), NumPy arrays are flattened, enums use their value, and
    objects with an ``svg_value`` method render themselves. Other types use `str`.

    Parameters
    ----------
    value : object
        The value to render.
    precision : int, optional
        Maximum number of decimal places for floats. Defaults to the library default precision.

    Returns
    -------
    str
        The attribute text.

    See Also
    --------
    svgwriter.model.attributes.SupportsSVG : Protocol for self-rendering objects.

    Examples
    --------
    >>> from svgwriter.model.attributes import format_value
    >>> format_value(1.5), format_value(True), format_value([1, 2.5])
    ('1.5', 'true', '1 2.5')
    >>> format_value([(1, 2), (3, 4)])
    '1,2 3,4'
    """
    if isinstance(value, SupportsSVG):
        return value.svg_value(precision)
    return str(value)


@format_value.register(str)
def _format_str(value: str, precision: int = DEFAULT_PRECISION) -> str:
    return value


@format_value.register(bool)
def _format_bool(value: bool, precision: int = DEFAULT_PRECISION) -> str:
    return "true" if value else "false"


@format_value.register(int)
def _format_int(value: int, precision: int = DEFAULT_PRECISION) -> str:
    return str(value)


@format_value.register(float)
def _format_float(value: float, precision: int = DEFAULT_PRECISION) -> str:
    return format_number(value, precision)


@format_value.register(enum.Enum)
def _format_enum(value: enum.Enum, precision: int = DEFAULT_PRECISION) -> str:
    if isinstance(value, SupportsSVG):
        return value.svg_value(precision)
    return format_value(value.value, precision)


@format_value.register(tuple)
@format_value.register(list)
def _format_sequence(value: tuple[object, ...] | list[object], precision: int = DEFAULT_PRECISION) -> str:
    parts = []
    for item in value:
        if isinstance(item, (tuple, list)):
            parts.append(",".join(format_value(part, precision) for part in item))
        else:
            parts.append(format_value(item, precision))
    return " ".join(parts)


@format_value.register(np.ndarray)
def _format_array(value: np.ndarray, precision: int = DEFAULT_PRECISION) -> str:
    if value.ndim == 2:
        return " ".join(",".join(format_number(float(v), precision) for v in row) for row in value)
    return " ".join(format_number(float(v), precision) for v in value.ravel())


@format_value.register(np.generic)
def _format_scalar(value: np.generic, precision: int = DEFAULT_PRECISION) -> str:
    return format_value(value.item(), precision)


@format_value.register(Mapping)
def _format_mapping(value: Mapping[str, object], precision: int = DEFAULT_PRECISION) -> str:
    from .style import Style

    return Style(value).svg_value(precision)
