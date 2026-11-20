"""
``Attr``: a data descriptor that stores values in ``element.attributes``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from .names import svg_name

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["Attr", "LengthAttr"]

T = TypeVar("T")


class Attr(Generic[T]):
    """Expose one SVG attribute as a Python attribute.

    Parameters
    ----------
    name : str, optional
        SVG attribute name; derived from the Python name when omitted.
    convert : callable, optional
        Applied to raw strings (for instance values read by the parser).
    default : object, optional
        Returned when the attribute is not set. Defaults to None.

    See Also
    --------
    LengthAttr : Attribute that reads lengths.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.Rect.width.key
    'width'
    >>> svg.Rect(width=3).width
    3.0
    """

    __slots__ = ("convert", "default", "name", "svg")

    def __init__(
        self,
        name: str | None = None,
        *,
        convert: Callable[[Any], T] | None = None,
        default: T | None = None,
    ) -> None:
        self.svg = name
        self.name = name or ""
        self.convert = convert
        self.default = default

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        if self.svg is None:
            self.svg = svg_name(name)

    @overload
    def __get__(self, obj: None, owner: type | None = None) -> Attr[T]: ...
    @overload
    def __get__(self, obj: Element, owner: type | None = None) -> T | None: ...
    def __get__(self, obj: Element | None, owner: type | None = None) -> Attr[T] | T | None:
        if obj is None:
            return self
        raw = obj.attributes.get(self.key)
        if raw is None:
            return self.default
        if self.convert is not None and isinstance(raw, str):
            return self.convert(raw)
        return raw

    def __set__(self, obj: Element, value: T | str | None) -> None:
        obj.set(self.key, value)

    def __delete__(self, obj: Element) -> None:
        obj.attributes.pop(self.key, None)

    @property
    def key(self) -> str:
        """The SVG attribute name this descriptor reads and writes.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Rect.stroke_width.key
        'stroke-width'
        """
        assert self.svg is not None
        return self.svg

    def __repr__(self) -> str:
        return f"Attr({self.key!r})"


class LengthAttr(Attr["float | Length"]):
    """A length attribute: reads a ``float`` when unitless, a :class:`~svgwriter.Length` when it has a unit.

    Takes the same parameters as `Attr`. Values that cannot be parsed as a
    length are returned unchanged.

    See Also
    --------
    Attr : The general attribute descriptor.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.Rect(width=5).width, svg.parse('<rect width="2mm"/>').width
    (5.0, Length(value=2.0, unit=<Unit.MM: 'mm'>))
    """

    __slots__ = ()

    def __get__(self, obj: Element | None, owner: type | None = None) -> Any:
        if obj is None:
            return self
        raw = obj.attributes.get(self.key)
        if raw is None:
            return self.default
        from .length import Length, Unit

        try:
            length = Length.parse(raw)
        except (TypeError, ValueError):
            return raw
        return length.value if length.unit is Unit.NONE else length
