"""
The ``Element`` base class and the element registry.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Final, Literal, TypeAlias, TypeVar, Union, overload

from .._internal._constants import DEFAULT_PRECISION
from .._internal._ids import next_id
from .._internal._registry import chainable
from .._internal._typing import ElementId
from ..attributes.names import KNOWN_ATTRIBUTES, UNSUPPORTED_ATTRIBUTES, svg_name
from ..attributes.reference import IRI, FuncIRI
from ..attributes.values import format_value
from ..color.color import Color, as_color
from ._categories import Category, ContentModel
from ._compose import Composable
from ._display import Displayable
from ._errors import UnknownAttributeError, UnknownKeywordError
from ._query import Queryable

if TYPE_CHECKING:
    from .structure import Use

__all__ = [
    "AttrValue",
    "Category",
    "Child",
    "ContentModel",
    "Element",
]

E = TypeVar("E", bound="Element")
T = TypeVar("T")
C = TypeVar("C", "Element", str)

AttrValue = Any
Child: TypeAlias = Union["Element", str]

HREF_ATTRIBUTES: Final = frozenset({"xlink:href"})
COLOR_OPACITY: Final = {
    "fill": "fill-opacity",
    "stroke": "stroke-opacity",
    "stop-color": "stop-opacity",
    "flood-color": "flood-opacity",
}
COLOR_ATTRIBUTES: Final = frozenset({*COLOR_OPACITY, "color", "lighting-color"})
_XML_NAME_RE: Final = re.compile(r"^[A-Za-z_][\w.\-]*$")


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
    from ..color._named import COLOR_ALIASES

    return COLOR_ALIASES.get(text.strip().lower(), text)


def _check_paint(key: str, text: str) -> None:
    """Raise a helpful ``ValueError`` when *text* is not a color or paint SVG understands."""
    from ..color._named import NAMED_COLORS
    from ..color.paint import parse_paint

    try:
        parse_paint(text)
    except ValueError:
        close = difflib.get_close_matches(text.strip().lower(), NAMED_COLORS, n=1)
        hint = f"; did you mean {close[0]!r}?" if close else "; use a name, #rrggbb, rgb(...), a 0-1 tuple or url(#id)"
        raise ValueError(f"{key}={text!r} is not a color{hint}") from None


class Element(Queryable, Displayable, Composable):
    """Base class for every SVG element.

    Attributes are kept in ``attributes`` under their SVG names; keyword
    arguments use Python spelling (``stroke_width``, ``class_``,
    ``xlink_href``) and are translated by :func:`svg_name`.

    Parameters
    ----------
    *children : Element or str
        Child elements and text nodes.
    id : str, optional
        The element id. Defaults to None.
    attrs : mapping, optional
        Extra attributes given by their SVG names. Defaults to None.
    **extra
        Any other attribute, Python spelling.

    Raises
    ------
    UnknownKeywordError
        If a keyword is not a known SVG attribute.

    See Also
    --------
    svgwriter.elements.container.Container : Elements that hold children.

    Examples
    --------
    >>> import svgwriter as svg
    >>> el = svg.rect(0, 0, 10, 10, stroke_width=2)
    >>> el.tag, el.attributes["stroke-width"]
    ('rect', 2)
    """

    tag: ClassVar[str] = ""
    _auto_id: bool = False
    _id_owner: Element | None = None
    namespace: ClassVar[str | None] = None
    category: ClassVar[Category] = Category.OTHER
    content: ClassVar[ContentModel] = ContentModel.ELEMENTS
    _registry: ClassVar[dict[str, type[Element]]] = {}

    def __init_subclass__(
        cls,
        *,
        tag: str | None = None,
        category: Category | None = None,
        content: ContentModel | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        if category is not None:
            cls.category = category
        if content is not None:
            cls.content = content
        if tag is not None:
            cls.tag = tag
            Element._registry[tag] = cls

    def __init__(
        self,
        *children: Child,
        id: str | None = None,
        attrs: Mapping[str, AttrValue] | None = None,
        **extra: AttrValue,
    ) -> None:
        self.attributes: dict[str, AttrValue] = {}
        self.children: list[Child] = []
        self.parent: Element | None = None
        if id is not None:
            self.id = id
        for name, value in (attrs or {}).items():
            self.set(name, value)
        for name in extra:
            key = svg_name(name)
            if key not in KNOWN_ATTRIBUTES and key not in UNSUPPORTED_ATTRIBUTES and not key.startswith(OPEN_PREFIXES):
                raise UnknownKeywordError(type(self).__name__, name)
        self.update(**extra)
        self.extend(children)

    def __getattr__(self, name: str) -> AttrValue:
        """Any SVG attribute by its Python name: ``el.stroke_width``, ``el.view_box``."""
        if name.startswith("__") or name.startswith("_") and not name.endswith("_") or name in _INSTANCE_FIELDS:
            raise AttributeError(name)
        key = svg_name(name)
        attributes = self.__dict__.get("attributes", {})
        if key in attributes:
            return attributes[key]
        if key in KNOWN_ATTRIBUTES:
            return None
        raise UnknownAttributeError(type(self).__name__, name, type(self))

    def __setattr__(self, name: str, value: AttrValue) -> None:
        if name in _INSTANCE_FIELDS or name.startswith("_") and not name.endswith("_") or hasattr(type(self), name):
            object.__setattr__(self, name, value)
            return
        key = svg_name(name)
        if key not in KNOWN_ATTRIBUTES and key not in self.attributes:
            raise UnknownAttributeError(type(self).__name__, name)
        self.set(key, value)

    def __delattr__(self, name: str) -> None:
        if name in self.__dict__ or hasattr(type(self), name):
            object.__delattr__(self, name)
        else:
            self.attributes.pop(svg_name(name), None)

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

    @property
    def animate(self) -> Any:
        """Animation presets for this element: ``el.animate.fade_in(1).spin(2, begin=1)``.

        Returns
        -------
        Motion
            Chainable presets that add SMIL animation children.

        Examples
        --------
        >>> import svgwriter as svg
        >>> _ = svg.rect(0, 0, 10, 10).animate.fade_in()
        """
        from ..builder._motion import Motion

        return Motion(self)

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
        if not _XML_NAME_RE.match(value):
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
        key = name if name.startswith("{") else svg_name(name)
        if key in UNSUPPORTED_ATTRIBUTES:
            raise ValueError(
                f"{key!r} is a scripting/browser attribute; svgwriter writes static graphics and does not support it"
            )
        if value is None:
            self.attributes.pop(key, None)
            return
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

    def append(self, child: C) -> C:
        """Append a child element or text node and return it.

        An element that already has a parent is moved. Elements referenced by
        the child but not yet placed are collected into the root ``<defs>``.

        Parameters
        ----------
        child : Element or str
            The child to append.

        Returns
        -------
        Element or str
            The appended child.

        Raises
        ------
        TypeError
            If the content model forbids the child, or it is not an element or str.

        See Also
        --------
        insert : Add a child at a given position.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group()
        >>> g.append(svg.circle(0, 0, 1)).tag
        'circle'
        """
        if isinstance(child, str):
            if ContentModel.TEXT not in self.content:
                raise TypeError(f"<{self.tag}> cannot contain text")
        elif isinstance(child, Element):
            if ContentModel.ELEMENTS not in self.content:
                raise TypeError(f"<{self.tag}> cannot contain elements")
            if child.parent is not None:
                child.parent.remove(child)
            child.parent = self
        else:
            raise TypeError(f"cannot append {type(child).__name__}")
        self.children.append(child)
        if isinstance(child, Element):
            self._define_references(child)
        return child

    def _define_references(self, subtree: Element) -> None:
        """Move unplaced elements referenced from *subtree* into the root's ``<defs>``."""
        root = self.root()
        if root.tag != "svg":
            return
        for element in subtree.iter():
            if element._auto_id and element._id_owner is not root:
                object.__setattr__(element, "_id_owner", root)
                element.attributes["id"] = root._auto_id_for(element.tag or "el", element)
            for value in list(element.attributes.values()):
                target = getattr(value, "element", None)
                if target is not None and target.parent is None and target is not root:
                    root.defs().append(target)  # type: ignore[attr-defined]

    def extend(self, children: Iterable[Child]) -> None:
        """Append every child in *children*.

        Parameters
        ----------
        children : iterable of Element or str
            The children to append, in order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group()
        >>> g.extend([svg.circle(0, 0, 1), svg.circle(1, 1, 1)])
        >>> len(g)
        2
        """
        for child in children:
            self.append(child)

    def insert(self, index: int, child: C) -> C:
        """Insert a child at *index* and return it.

        Parameters
        ----------
        index : int
            Position among the children.
        child : Element or str
            The child to insert.

        Returns
        -------
        Element or str
            The inserted child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1))
        >>> _ = g.insert(0, svg.rect(0, 0, 1, 1))
        >>> [c.tag for c in g]
        ['rect', 'circle']
        """
        self.append(child)
        self.children.insert(index, self.children.pop())
        return child

    def remove(self, child: Child) -> None:
        """Remove a child and detach it from this element.

        Parameters
        ----------
        child : Element or str
            The child to remove.

        Raises
        ------
        ValueError
            If the child is not present.

        Examples
        --------
        >>> import svgwriter as svg
        >>> c = svg.circle(0, 0, 1)
        >>> g = svg.group(c)
        >>> g.remove(c)
        >>> len(g)
        0
        """
        self.children.remove(child)
        if isinstance(child, Element):
            child.parent = None

    def clear(self) -> None:
        """Remove and detach every child.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1))
        >>> g.clear()
        >>> len(g)
        0
        """
        for child in self.children:
            if isinstance(child, Element):
                child.parent = None
        self.children.clear()

    @property
    def text_content(self) -> str:
        """All character data below this element, in document order (the DOM ``textContent``).

        Assigning replaces every child with the single string.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("Hello world")
        >>> t[6:].fill = "red"
        >>> t.text_content
        'Hello world'
        >>> title = svg.Title("Old")
        >>> title.text_content = "New"
        >>> str(title)
        '<title>New</title>'
        """
        return "".join(c if isinstance(c, str) else c.text_content for c in self.children)

    @text_content.setter
    def text_content(self, value: str) -> None:
        self.clear()
        if value:
            self.append(value)  # type: ignore[arg-type]

    def computed(self, name: str, default: object = None) -> object:
        """The value SVG would use for property *name* (SVG spelling or Python spelling).

        Looks at the inline ``style``, matching ``<style>`` rules, the
        presentation attribute, then ancestors for inherited properties.

        Parameters
        ----------
        name : str
            Property name, in SVG (``font-size``) or Python (``font_size``) spelling.
        default : object, optional
            Returned when the property is not set anywhere. Defaults to None.

        Returns
        -------
        object
            The property's value, written as SVG text when it is not a plain number,
            or *default*.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(fill="red", font_size=30)
        >>> t = g.add(svg.text("hi", style="font-size: 12px"))
        >>> t.computed("fill"), t.computed("font_size"), t.computed("opacity", 1)
        ('red', '12px', 1)
        """
        from ..attributes.cascade import computed

        value = computed(self, svg_name(name), default)
        return value.svg_value() if hasattr(value, "svg_value") and not isinstance(value, (int, float)) else value

    @overload
    def clone(self: E, linked: Literal[False] = False) -> E: ...
    @overload
    def clone(self, linked: Literal[True]) -> Use: ...
    def clone(self, linked: bool = False) -> Element:
        """A deep, detached copy; or with *linked*, a ``<use>`` that renders this element.

        Parameters
        ----------
        linked : bool
            ``False`` copies the whole subtree (pixels included), so edits
            never reach the original. ``True`` returns a ``<use>``
            referencing this element (giving it an id), so edits to the
            original show through every linked clone.

        Returns
        -------
        Element
            A copy of the same class, or a :class:`~svgwriter.Use`.

        Notes
        -----
        A linked clone needs the original in the same document: placed
        anywhere, or unplaced, in which case it moves into ``<defs>`` when
        the ``<use>`` joins the document. ``copy.copy`` and ``copy.deepcopy``
        both behave like ``clone()``.

        Examples
        --------
        >>> import svgwriter as svg
        >>> star = svg.circle(0, 0, 5, id="dot")
        >>> star.clone().id, star.clone(linked=True).tag
        ('dot', 'use')
        """
        if linked:
            from .structure import Use

            return Use(self)
        duplicate = type(self).__new__(type(self))
        object.__setattr__(duplicate, "__dict__", dict(self.__dict__))
        duplicate.attributes = {
            k: v.clone() if hasattr(v, "clone") and not isinstance(v, Element) else v
            for k, v in self.attributes.items()
        }
        object.__setattr__(duplicate, "_id_owner", None)
        duplicate.parent = None
        duplicate.children = []
        for child in self.children:
            if isinstance(child, Element):
                copied = child.clone()
                copied.parent = duplicate
                duplicate.children.append(copied)
            else:
                duplicate.children.append(child)
        return duplicate

    copy = clone
    """Same as :meth:`clone`."""

    def __copy__(self: E) -> E:
        return self.clone()

    def __deepcopy__(self: E, memo: dict[int, object]) -> E:
        return self.clone()


OPEN_PREFIXES: Final = ("data-", "aria-")
_INSTANCE_FIELDS: Final = frozenset({"attributes", "children", "parent"})


@format_value.register(Element)
def _format_element(value: Element, precision: int = DEFAULT_PRECISION) -> str:
    return value.url.svg_value(precision)
