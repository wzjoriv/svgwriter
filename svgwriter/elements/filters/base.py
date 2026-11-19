"""
``<filter>`` and the shared filter-primitive base classes.
"""

from __future__ import annotations

import enum
from typing import Any, TypeAlias, Union

from ..._internal._typing import Units
from .._mixins import CoreAttributes, ExternalResourcesAttribute, PresentationAttributes, XLinkAttributes
from .._viewport import Positioned
from ..base import Category, Child, Element
from ..container import Container

__all__ = [
    "Filter",
    "FilterInput",
    "FilterPrimitive",
    "SingleInput",
    "StandardInput",
    "TwoInputs",
    "resolve_input",
]


class StandardInput(str, enum.Enum):
    """Keywords accepted by ``in`` and ``in2``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.StandardInput.SOURCE_ALPHA.value
    'SourceAlpha'
    """

    SOURCE_GRAPHIC = "SourceGraphic"
    SOURCE_ALPHA = "SourceAlpha"
    BACKGROUND_IMAGE = "BackgroundImage"
    BACKGROUND_ALPHA = "BackgroundAlpha"
    FILL_PAINT = "FillPaint"
    STROKE_PAINT = "StrokePaint"


FilterInput: TypeAlias = Union[StandardInput, str, "FilterPrimitive"]


def resolve_input(value: FilterInput | None) -> StandardInput | str | None:
    """Turn a primitive into the name of its result.

    Referring to a primitive by element lets its ``result`` name be generated
    on demand; keywords and strings pass through unchanged.

    Parameters
    ----------
    value : StandardInput, str, FilterPrimitive or None
        An input keyword, a result name or the primitive producing the input.

    Returns
    -------
    StandardInput, str or None
        The result name for a primitive, otherwise `value` itself.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.resolve_input(svg.FeOffset(id="shift"))
    'shift-out'
    >>> svg.resolve_input("SourceAlpha")
    'SourceAlpha'
    """
    if isinstance(value, FilterPrimitive):
        return value.result
    return value


class FilterPrimitive(Positioned, PresentationAttributes, CoreAttributes, category=Category.FILTER_PRIMITIVE):
    """Base of every ``fe*`` element: sub-region and ``result`` name.

    Parameters
    ----------
    *args : Element
        Initial children.
    result : str, optional
        Name later primitives use to refer to this output. Defaults to None,
        which generates one on first access.
    **kwargs
        Sub-region (``x``, ``y``, ``width``, ``height``), presentation, core
        and other SVG attributes in Python spelling.

    See Also
    --------
    Filter : The container that holds primitives.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeOffset(result="shifted"))
    '<feOffset result="shifted" dx="0" dy="0"/>'
    """

    def __init__(self, *args: Child, result: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(result=result)

    @property
    def result(self) -> str:
        """The result name, generated on first access if unset.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.FeOffset(id="shift").result
        'shift-out'
        """
        name = self.attributes.get("result")
        if name is None:
            name = self.ensure_id() + "-out"
            self.attributes["result"] = name
        return str(name)

    def _input(self, name: str, value: FilterInput | None) -> None:
        self.update({name: resolve_input(value)})


class SingleInput(FilterPrimitive):
    """Primitives that read one input (``in``).

    Parameters
    ----------
    *args : Element
        Initial children.
    in_ : StandardInput, str or FilterPrimitive, optional
        The input: a keyword, a result name or the primitive producing it.
        Defaults to None, meaning the previous primitive's result.
    **kwargs
        ``result``, sub-region and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeOffset(in_="SourceAlpha"))
    '<feOffset in="SourceAlpha" dx="0" dy="0"/>'
    """

    def __init__(self, *args: Child, in_: FilterInput | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._input("in", in_)


class TwoInputs(SingleInput):
    """Primitives that combine ``in`` and ``in2``.

    Parameters
    ----------
    *args : Element
        Initial children.
    in2 : StandardInput, str or FilterPrimitive, optional
        The second input. Defaults to None.
    **kwargs
        ``in_``, ``result``, sub-region and other SVG attributes in Python spelling.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.FeBlend(in_="SourceGraphic", in2="shade"))
    '<feBlend in="SourceGraphic" in2="shade"/>'
    """

    def __init__(self, *args: Child, in2: FilterInput | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._input("in2", in2)


class Filter(
    XLinkAttributes,
    Positioned,
    PresentationAttributes,
    ExternalResourcesAttribute,
    CoreAttributes,
    Container[Element],
    tag="filter",
    category=Category.CONTAINER,
):
    """``<filter>``: a graph of filter primitives.

    Parameters
    ----------
    *primitives : FilterPrimitive
        The primitives, in evaluation order.
    filter_units, primitive_units : {"userSpaceOnUse", "objectBoundingBox"}, optional
        Coordinate systems for the region and the primitives.
    filter_res : float or (float, float), optional
        Intermediate image resolution.
    **kwargs
        Region (``x``, ``y``, ``width``, ``height``), ``href`` and
        presentation/core attributes in Python spelling.

    See Also
    --------
    FilterPrimitive : Base of the elements a filter contains.

    Examples
    --------
    >>> import svgwriter as svg
    >>> str(svg.Filter(svg.FeGaussianBlur(std_deviation=1), id="soft"))
    '<filter id="soft"><feGaussianBlur stdDeviation="1"/></filter>'
    """

    def __init__(
        self,
        *primitives: Child,
        filter_units: Units | None = None,
        primitive_units: Units | None = None,
        filter_res: float | tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*primitives, **kwargs)
        self.update(filter_units=filter_units, primitive_units=primitive_units, filter_res=filter_res)

    @property
    def primitives(self) -> list[FilterPrimitive]:
        """The filter-primitive children in evaluation order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Filter(svg.FeOffset(), svg.FeTile()).primitives
        [<FeOffset feOffset dx='0' dy='0'>, <FeTile feTile>]
        """
        return [c for c in self if isinstance(c, FilterPrimitive)]
