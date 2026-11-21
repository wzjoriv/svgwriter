"""
``<filter>`` and the shared filter-primitive base classes.
"""

from __future__ import annotations

from typing import Any, TypeAlias, Union

from ..._internal._enums import Keyword
from ..._internal._typing import Self, Units
from .._behavior import (
    CoreAttributes,
    ExternalResourcesAttribute,
    Positioned,
    PresentationAttributes,
    XLinkAttributes,
)
from ..core import Category, Child, Container, Element

__all__ = [
    "Filter",
    "FilterInput",
    "FilterPrimitive",
    "SingleInput",
    "StandardInput",
    "TwoInputs",
    "resolve_input",
]


class StandardInput(Keyword):
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
        self._assign(result=result)

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
        remember_source(self, name, value)
        self.update({name: resolve_input(value)})

    def sources(self) -> list[FilterPrimitive]:
        """The primitives this one reads, directly or through merge nodes, nearest first.

        Returns
        -------
        list of FilterPrimitive
            Every upstream primitive given as an input object (not by name).

        Examples
        --------
        >>> import svgwriter as svg
        >>> blur = svg.FeGaussianBlur(2, in_="SourceAlpha")
        >>> shifted = svg.FeOffset(2, 2, in_=blur)
        >>> shifted.sources() == [blur]
        True
        """
        found: list[FilterPrimitive] = []
        pending = [self]
        while pending:
            node = pending.pop()
            for item in (node, *node.iter()):
                for source in getattr(item, "_sources", {}).values():
                    if all(source is not seen for seen in found):
                        found.append(source)
                        pending.append(source)
        return found

    def __rshift__(self, other: FilterPrimitive) -> FilterPrimitive:
        """``a >> b``: *b* reads *a* (its ``in``, or the next free merge layer) and is returned for chaining."""
        if not isinstance(other, FilterPrimitive):
            return NotImplemented
        other._feed(self)
        return other

    def _feed(self, source: FilterPrimitive) -> None:
        self._input("in", source)


def remember_source(owner: Element, name: str, value: object) -> None:
    """Keep the primitive object behind an input so a :class:`Filter` can collect it later."""
    sources = owner.__dict__.setdefault("_sources", {})
    if isinstance(value, FilterPrimitive):
        sources[name] = value
    else:
        sources.pop(name, None)


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
        self._assign(filter_units=filter_units, primitive_units=primitive_units, filter_res=filter_res)
        self.collect()

    def collect(self) -> Self:
        """Insert every detached primitive the filter's primitives read, before its first reader.

        ``Filter(merge)`` is then enough: the blur and offset that feed the
        merge come along in dependency order.

        Returns
        -------
        Filter
            This filter, for chaining.

        Examples
        --------
        >>> import svgwriter as svg
        >>> blur = svg.FeGaussianBlur(3, in_="SourceAlpha")
        >>> shadow = svg.FeOffset(2, 2, in_=blur)
        >>> f = svg.Filter(svg.FeMerge(shadow, "SourceGraphic"))
        >>> [p.tag for p in f.primitives]
        ['feGaussianBlur', 'feOffset', 'feMerge']
        """
        index = 0
        while index < len(self.children):
            child = self.children[index]
            missing = [s for s in getattr(child, "sources", list)() if s.parent is None] if isinstance(
                child, FilterPrimitive) else []
            if not missing:
                index += 1
                continue
            self.insert(index, missing[0])
        return self

    def __rshift__(self, other: Filter) -> Filter:
        """``f1 >> f2``: one filter applying *f1*, then *f2* to its result.

        SVG 1.1 allows a single ``filter`` per element, so this is how effects
        stack: copies of *f2*'s primitives read *f1*'s output wherever they
        read ``SourceGraphic`` (explicitly or as the first primitive).
        """
        if not isinstance(other, Filter):
            return NotImplemented
        first = [p.clone() for p in self.primitives]
        second = [p.clone() for p in other.primitives]
        last = first[-1].result if first else StandardInput.SOURCE_GRAPHIC.value
        for position, primitive in enumerate(second):
            for node in (primitive, *primitive.iter()):
                for name in ("in", "in2"):
                    value = node.get(name)
                    if value == StandardInput.SOURCE_GRAPHIC.value or (
                            position == 0 and name == "in" and value is None and isinstance(node, SingleInput)):
                        node.set(name, last)
        return Filter(*first, *second)

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
