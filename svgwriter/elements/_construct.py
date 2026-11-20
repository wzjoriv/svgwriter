"""
Class-level construction for ``Element``: tag lookup, the registry and batch creation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ..attributes.names import svg_name
from ._access import _check_paint, _color_column
from ._categories import Category
from ._constants import COLOR_ATTRIBUTES, COLOR_OPACITY

if TYPE_CHECKING:
    from .base import E, Element

__all__ = ["Construction"]


class Construction:
    """Tag lookup, registry queries and ``many``; mixed into :class:`~svgwriter.elements.base.Element`."""

    __slots__ = ()

    @classmethod
    def lookup(cls, tag: str) -> type[Element] | None:
        """Return the registered class for *tag*.

        Parameters
        ----------
        tag : str
            An SVG tag name.

        Returns
        -------
        type[Element] or None
            The class registered for the tag, or None if there is none.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Element.lookup("rect").__name__
        'Rect'
        """
        return cls._registry.get(tag)

    @classmethod
    def registered(cls, category: Category | None = None) -> dict[str, type[Element]]:
        """Registered element classes, optionally filtered by category.

        Parameters
        ----------
        category : Category, optional
            Keep only classes of this category. Defaults to None (all).

        Returns
        -------
        dict[str, type[Element]]
            Registered classes keyed by tag.

        Examples
        --------
        >>> import svgwriter as svg
        >>> "circle" in svg.Element.registered()
        True
        """
        return {
            tag: klass for tag, klass in cls._registry.items()
            if category is None or klass.category is category
        }

    @classmethod
    def from_attributes(cls: type[E], attributes: Mapping[str, str]) -> E:
        """Build an instance from raw SVG attributes, bypassing ``__init__``.

        Parameters
        ----------
        attributes : mapping of str to str
            Attributes by SVG name, stored as given.

        Returns
        -------
        Element
            A new instance of this class.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Rect.from_attributes({"width": "5"}).attributes
        {'width': '5'}
        """
        from .base import Element

        obj = cls.__new__(cls)
        Element.__init__(obj)
        obj.attributes.update(attributes)
        return obj

    @classmethod
    def many(cls: type[E], **columns: Any) -> list[E]:
        """Build many elements at once from columns that broadcast like numpy.

        Each keyword is an attribute in Python spelling; a scalar applies to
        every element and an array gives one value per element. Colors may be
        one color, a list of colors or an ``(n, 3|4)`` array of 0-1 floats.

        Parameters
        ----------
        **columns
            Attribute name to scalar or sequence.

        Returns
        -------
        list of Element
            The new elements, ready for ``doc.group(*elements)`` or ``doc.add_all``.

        Raises
        ------
        ValueError
            If the columns do not broadcast to one length.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> dots = svg.Circle.many(cx=np.arange(3) * 10, cy=5, r=2, fill=["red", "green", "blue"])
        >>> [str(d) for d in dots][1]
        '<circle cx="10" cy="5" r="2" fill="green"/>'
        """
        import numpy as np

        prepared: dict[str, Any] = {}
        for name, value in columns.items():
            key = svg_name(name)
            if key in COLOR_ATTRIBUTES and isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
                for text in value:
                    _check_paint(key, text)
                prepared[key] = list(value)
                continue
            if key in COLOR_ATTRIBUTES and not isinstance(value, str):
                colors = _color_column(value)
                prepared[key] = [color.opaque.hex for color in colors] if len(colors) > 1 else colors[0].opaque.hex
                if key in COLOR_OPACITY and any(color.a < 1 for color in colors):
                    alphas = [color.a for color in colors]
                    prepared[COLOR_OPACITY[key]] = alphas if len(alphas) > 1 else alphas[0]
                continue
            prepared[key] = value
        lengths = {len(v) for v in prepared.values() if isinstance(v, (list, tuple, np.ndarray))}
        if len(lengths) > 1:
            raise ValueError(f"columns have different lengths {sorted(lengths)}; scalars broadcast, arrays must match")
        count = lengths.pop() if lengths else 1
        rows = []
        for index in range(count):
            row = {}
            for key, value in prepared.items():
                item = value[index] if isinstance(value, (list, tuple, np.ndarray)) else value
                row[key] = item.item() if isinstance(item, np.generic) else item
            rows.append(cls.from_attributes(row))
        return rows
