"""
Filter primitive bases and how primitives name their inputs.
"""

from __future__ import annotations

from typing import Any, TypeAlias, Union

from ...._internal._enums import Keyword
from .._behavior import (
    CoreAttributes,
    Positioned,
    PresentationAttributes,
)
from ..core import Category, Child, Element

__all__ = ["FilterInput", "FilterPrimitive", "SingleInput", "StandardInput", "TwoInputs", "remember_source", "resolve_input"]


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
