"""
Attribute access for ``Element``: ids, references and ``set``/``get``/``has``/``discard``.
"""

from __future__ import annotations

import difflib
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, overload

from ..._internal._ids import next_id
from ..._internal._registry import chainable
from ..._internal._typing import ElementId
from ...attributes.names import UNSUPPORTED_ATTRIBUTES, svg_name
from ...attributes.quantity import check_dimension
from ...attributes.reference import IRI, FuncIRI
from ...color.color import Color, as_color
from ._categories import Category
from ._constants import COLOR_ATTRIBUTES, COLOR_OPACITY, HREF_ATTRIBUTES, XML_NAME_RE

if TYPE_CHECKING:
    from ._element import AttrValue, Element, T

__all__ = ["AttributeAccess"]


def _color_column(value: Any) -> list[Color]:
    """One color, a list of colors, or an ``(n, 3|4)`` array of 0-1 floats, as a list of colors."""
    import numpy as np

    if isinstance(value, Color):
        return [value]
    if isinstance(value, np.ndarray) and value.ndim == 2:
        return [as_color(tuple(float(v) for v in row)) for row in value]
    items = list(value)
    if items and all(isinstance(v, (int, float, np.floating)) for v in items):
        return [as_color(tuple(float(v) for v in items))]
    return [as_color(item) for item in items]


def _standard_name(text: str) -> str:
    """An svgwriter color alias (``"masooma"``) as the SVG keyword it stands for; other text unchanged."""
    from ..._internal._constants import COLOR_ALIASES

    return COLOR_ALIASES.get(text.strip().lower(), text)


def _check_paint(key: str, text: str) -> None:
    """Raise a helpful ``ValueError`` when *text* is not a color or paint SVG understands."""
    from ...color import NAMED_COLORS
    from ...color.paint import parse_paint

    try:
        parse_paint(text)
    except ValueError:
        close = difflib.get_close_matches(text.strip().lower(), NAMED_COLORS, n=1)
        hint = f"; did you mean {close[0]!r}?" if close else "; use a name, #rrggbb, rgb(...), a 0-1 tuple or url(#id)"
        raise ValueError(f"{key}={text!r} is not a color{hint}") from None


class AttributeAccess:
    """Ids, references and attribute reads and writes; mixed into :class:`~svgwriter.elements.Element`."""

    __slots__ = ()

    @property
    def id(self) -> str | None:
        """The element id, or None.

        Assigning validates the name as an XML name; assigning None removes it.

        Raises
        ------
        ValueError
            On assignment, if the value is not a valid id.

        Examples
        --------
        >>> import svgwriter as svg
        >>> el = svg.rect(0, 0, 1, 1, id="a")
        >>> el.id
        'a'
        """
        value = self.attributes.get("id")
        return None if value is None else str(value)

    @id.setter
    def id(self, value: str | None) -> None:
        self._auto_id = False
        if value is None:
            self.attributes.pop("id", None)
            return
        if not XML_NAME_RE.match(value):
            raise ValueError(f"invalid id: {value!r}")
        self.attributes = {"id": value, **{k: v for k, v in self.attributes.items() if k != "id"}}

    def ensure_id(self) -> ElementId:
        """Return the id, assigning a generated one if needed.

        Returns
        -------
        str
            The existing or newly generated id.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1, id="a").ensure_id()
        'a'
        """
        if self.id is None:
            root = self.root()
            if root.tag == "svg":
                self.id = root._auto_id_for(self.tag or "el")
                self._id_owner = root
            else:
                self.id = next_id(self.tag or "el")
                self._id_owner = None
            self._auto_id = True
        return ElementId(self.id or "")

    def _auto_id_for(self, prefix: str, owner: Element | None = None) -> str:
        """The next free ``prefixN`` id numbered within this (root) element's document (*owner* may keep its own)."""
        counts: dict[str, int] = self.__dict__.setdefault("_id_counts", {})
        while True:
            counts[prefix] = counts.get(prefix, 0) + 1
            candidate = f"{prefix}{counts[prefix]}"
            holder = self.get_element_by_id(candidate)
            if holder is None or holder is owner:
                return candidate

    @property
    def url(self) -> FuncIRI:
        """``url(#id)`` pointing at this element, assigning an id if needed.

        Use it where SVG expects a functional IRI (``fill``, ``clip-path``, ``filter``); passing the
        element itself does the same.

        See Also
        --------
        iri : The plain ``#id`` form.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1, id="a").url.svg_value()
        'url(#a)'
        """
        return FuncIRI("#" + self.ensure_id(), self)

    @property
    def iri(self) -> IRI:
        """``#id`` pointing at this element, assigning an id if needed.

        Use it where SVG expects a plain IRI (``xlink:href`` of ``<use>``, ``<mpath>``, ...); passing
        the element itself does the same. An element's own ``xlink:href`` is ``el.href``.

        See Also
        --------
        url : The ``url(#id)`` form.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1, id="a").iri.svg_value()
        '#a'
        """
        return IRI("#" + self.ensure_id(), self)

    @chainable
    def set(self, name: str, value: AttrValue) -> None:
        """Set one attribute; ``None`` removes it.

        Attributes in other namespaces use Clark notation: ``"{uri}name"``.
        Colors with alpha are split into the color and its ``*-opacity``
        attribute, and elements are replaced by references to them.

        Parameters
        ----------
        name : str
            The attribute name, Python or SVG spelling.
        value : object
            The new value; None removes the attribute.

        Raises
        ------
        TypeError
            If a length, angle or `~svgwriter.Quantity` has the wrong
            dimension for the attribute (``width`` given an area).
        ValueError
            If the attribute is unsupported, a color string is not a valid
            color or paint, or a color with alpha is given to an attribute
            without an opacity counterpart.

        See Also
        --------
        update : Set several attributes at once.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1)
        >>> _ = r.set("stroke_width", 3)
        >>> r.attributes["stroke-width"]
        3
        """
        from ._element import Element

        key = name if name.startswith("{") else svg_name(name)
        if key in UNSUPPORTED_ATTRIBUTES:
            raise ValueError(
                f"{key!r} is a scripting/browser attribute; svgwriter writes static graphics and does not support it"
            )
        if value is None:
            self.attributes.pop(key, None)
            return
        if key == "font" and _is_typeface(value):
            key = "font-family"
        check_dimension(key, value)
        if key in COLOR_ATTRIBUTES and isinstance(value, str):
            if not (key == "fill" and self.category is Category.ANIMATION):
                _check_paint(key, value)
                value = _standard_name(value)
        elif key in COLOR_ATTRIBUTES and not isinstance(value, Element) and not hasattr(value, "svg_value"):
            value = as_color(value)
        if isinstance(value, Color) and value.a < 1.0 and key in COLOR_ATTRIBUTES:
            if key not in COLOR_OPACITY:
                raise ValueError(f"{key} has no opacity in SVG 1.1; use an opaque color")
            self.attributes[COLOR_OPACITY[key]] = value.a
            value = value.opaque
        if isinstance(value, Element):
            value = value.iri if key in HREF_ATTRIBUTES else value.url
        elif isinstance(value, FuncIRI) and key in HREF_ATTRIBUTES:
            value = IRI(value.target, value.element)
        self.attributes[key] = value
        if getattr(value, "element", None) is not None:
            self._define_references(self)

    @chainable
    def update(self, attributes: Mapping[str, AttrValue] | None = None, /, **kwargs: AttrValue) -> None:
        """Set several attributes; ``None`` values are skipped.

        Parameters
        ----------
        attributes : mapping, optional
            Attributes by name. Defaults to None.
        **kwargs
            More attributes, Python spelling.

        See Also
        --------
        set : Set a single attribute.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1)
        >>> _ = r.update(fill="red", stroke=None)
        >>> r.get("fill")
        'red'
        """
        for name, value in {**(attributes or {}), **kwargs}.items():
            if value is not None:
                self.set(name, value)

    @overload
    def get(self, name: str) -> AttrValue | None: ...
    @overload
    def get(self, name: str, default: T) -> AttrValue | T: ...
    def get(self, name: str, default: object = None) -> object:
        """Return an attribute value, or *default* if it is not set.

        Parameters
        ----------
        name : str
            The attribute name, Python or SVG spelling.
        default : object, optional
            Returned when the attribute is absent. Defaults to None.

        Returns
        -------
        object
            The stored value or the default.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1, stroke_width=2)
        >>> r.get("stroke_width"), r.get("fill", "none")
        (2, 'none')
        """
        return self.attributes.get(svg_name(name), default)

    def has(self, name: str) -> bool:
        """Report whether an attribute is set.

        Parameters
        ----------
        name : str
            The attribute name, Python or SVG spelling.

        Returns
        -------
        bool
            True if the attribute is present.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1).has("width")
        True
        """
        return svg_name(name) in self.attributes

    def discard(self, name: str) -> None:
        """Remove an attribute if it is set.

        Parameters
        ----------
        name : str
            The attribute name, Python or SVG spelling.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1)
        >>> r.discard("width")
        >>> r.has("width")
        False
        """
        self.attributes.pop(svg_name(name), None)


def _is_typeface(value: object) -> bool:
    """Whether *value* is a :class:`~svgwriter.ops.Typeface`, which ``font=`` sets as the family."""
    from ...ops.typeface import Typeface

    return isinstance(value, Typeface)
