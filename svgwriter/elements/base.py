"""
The ``Element`` base class and the element registry.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Iterable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Final, Literal, TypeAlias, TypeVar, Union, overload

from .._internal._constants import DEFAULT_PRECISION
from .._internal._ids import next_id
from .._internal._registry import chainable
from .._internal._typing import ElementId
from ..attributes.names import KNOWN_ATTRIBUTES, UNSUPPORTED_ATTRIBUTES, py_name, svg_name
from ..attributes.reference import IRI, FuncIRI
from ..attributes.values import format_value
from ..color.color import Color, as_color
from ._categories import Category, ContentModel
from ._compose import Composable

if TYPE_CHECKING:
    from .._internal._typing import AnyPath
    from ..attributes.protocols import TextSink
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
SUGGESTIONS: Final = 3
PREVIEW_PADDING: Final = 2.0
PREVIEW_SCALE: Final = 1.0
PREVIEW_MIN_PIXELS: Final = 200.0
_XML_NAME_RE: Final = re.compile(r"^[A-Za-z_][\w.\-]*$")


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


class Element(Composable):
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

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[Element]:
        return (c for c in self.children if isinstance(c, Element))

    def __bool__(self) -> bool:
        return True

    def iter(self, tag: str | None = None, *, max_depth: float = float("inf")) -> Iterator[Element]:
        """Depth-first walk over this element and its descendants.

        Parameters
        ----------
        tag : str, optional
            Yield only elements with this tag. Defaults to None (all).
        max_depth : float, optional
            Deepest level to descend to; ``0`` is this element only.
            Defaults to infinity.

        Yields
        ------
        Element
            Elements in document order, starting with this one.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1), svg.rect(0, 0, 1, 1))
        >>> [e.tag for e in g.iter()]
        ['g', 'circle', 'rect']
        """
        stack: list[tuple[Element, int]] = [(self, 0)]
        while stack:
            element, depth = stack.pop()
            if tag is None or element.tag == tag:
                yield element
            if depth < max_depth:
                stack.extend(
                    (child, depth + 1) for child in reversed(element.children) if isinstance(child, Element)
                )

    @overload
    def find(self, match: type[E]) -> E | None: ...
    @overload
    def find(self, match: str) -> Element | None: ...
    def find(self, match: type[Element] | str) -> Element | None:
        """First descendant (or self) matching a tag or class.

        Parameters
        ----------
        match : str or type
            A tag name or an element class.

        Returns
        -------
        Element or None
            The first match in document order, or None.

        See Also
        --------
        find_all : Every match.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1))
        >>> g.find("circle").tag, g.find("rect")
        ('circle', None)
        """
        return next(iter(self.find_all(match)), None)

    @overload
    def find_all(self, match: type[E]) -> list[E]: ...
    @overload
    def find_all(self, match: str) -> list[Element]: ...
    def find_all(self, match: type[Element] | str) -> list[Element]:
        """Every descendant (and self) matching a tag or class.

        Parameters
        ----------
        match : str or type
            A tag name or an element class.

        Returns
        -------
        list of Element
            The matches in document order.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1), svg.circle(1, 1, 1))
        >>> len(g.find_all("circle"))
        2
        """
        if isinstance(match, str):
            return list(self.iter(match))
        return [e for e in self.iter() if isinstance(e, match)]

    def get_element_by_id(self, element_id: str) -> Element | None:
        """Find the element with the given id in this subtree.

        Parameters
        ----------
        element_id : str
            The id to look for.

        Returns
        -------
        Element or None
            The matching element, or None.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(svg.circle(0, 0, 1, id="dot"))
        >>> g.get_element_by_id("dot").tag
        'circle'
        """
        return next((e for e in self.iter() if e.id == element_id), None)

    def root(self) -> Element:
        """Return the topmost ancestor, or this element if it has no parent.

        Returns
        -------
        Element
            The root of the tree this element belongs to.

        Examples
        --------
        >>> import svgwriter as svg
        >>> c = svg.circle(0, 0, 1)
        >>> g = svg.group(c)
        >>> c.root() is g
        True
        """
        node = self
        while node.parent is not None:
            node = node.parent
        return node

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

    def to_string(self, **options: Any) -> str:
        """Serialize to an SVG string; see :class:`svgwriter.io.SerializeOptions`.

        Parameters
        ----------
        **options
            Serialization options such as ``pretty`` or ``xml_declaration``.

        Returns
        -------
        str
            The SVG markup.

        See Also
        --------
        save : Write to a file or stream.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.circle(0, 0, 1).to_string(xml_declaration=False, pretty=False)
        '<circle cx="0" cy="0" r="1"/>'
        """
        from ..io.writer import to_string

        return to_string(self, **options)

    def save(self, target: AnyPath | TextSink, **options: Any) -> None:
        """Write to a path or text stream.

        Parameters
        ----------
        target : path or text stream
            Where to write the SVG markup.
        **options
            Serialization options, as for :meth:`to_string`.

        See Also
        --------
        to_string : Serialize to a string.

        Examples
        --------
        >>> import io
        >>> import svgwriter as svg
        >>> buffer = io.StringIO()
        >>> svg.circle(0, 0, 1).save(buffer, xml_declaration=False, pretty=False)
        >>> buffer.getvalue()
        '<circle cx="0" cy="0" r="1"/>'
        """
        from ..io.writer import write

        write(self, target, **options)

    def _preview(self) -> Any:
        """A copy of this element alone in a fitted document, enlarged to at least 200 px on its longer side."""
        from ..document import Document

        doc = Document()
        doc.add(self.clone())
        doc.fit(padding=PREVIEW_PADDING)
        box = doc.root.view_box
        longest = max(box.width, box.height) if box is not None else 0.0
        if 0 < longest < PREVIEW_MIN_PIXELS:
            zoom = PREVIEW_MIN_PIXELS / longest
            doc.root.set("width", box.width * zoom)
            doc.root.set("height", box.height * zoom)
        return doc

    def _repr_svg_(self) -> str:
        """Jupyter display: the element alone in a fitted ``<svg>`` (an ``<svg>`` root shows as itself)."""
        if self.tag == "svg":
            return self.to_string(xml_declaration=False)
        return self._preview().to_string(xml_declaration=False)

    def _repr_png_(self) -> bytes | None:
        """Jupyter display as PNG, for front ends that do not show SVG; None when there is nothing to draw."""
        try:
            return self._preview().render_png(scale=PREVIEW_SCALE)
        except (TypeError, ValueError):
            return None

    def __str__(self) -> str:
        return self.to_string(xml_declaration=False, pretty=False)

    def __repr__(self) -> str:
        shown = " ".join(f"{k}={format_value(v)!r}" for k, v in list(self.attributes.items())[:3])
        return f"<{type(self).__name__} {self.tag}{' ' + shown if shown else ''}>"


OPEN_PREFIXES: Final = ("data-", "aria-")
_INSTANCE_FIELDS: Final = frozenset({"attributes", "children", "parent"})
_PY_NAMES: Final = sorted({py_name(n) for n in KNOWN_ATTRIBUTES})


class UnknownAttributeError(AttributeError):
    """An attribute that is neither a Python member nor a known SVG attribute.

    The "did you mean" suggestion is computed only when the message is shown,
    so ``getattr(element, name, default)`` stays cheap.

    Parameters
    ----------
    owner : str
        The class name of the element.
    name : str
        The attribute that was requested.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.rect(0, 0, 1, 1).widht
    ... except AttributeError as error:
    ...     print("did you mean 'width'?" in str(error))
    True
    """

    def __init__(self, owner: str, name: str, members: type | None = None) -> None:
        super().__init__(name)
        self.owner = owner
        self.attribute = name
        self.members = members

    def __str__(self) -> str:
        methods = [m for m in dir(self.members) if not m.startswith("_")] if self.members is not None else []
        hint = [m for m in methods if m.startswith(self.attribute)][:SUGGESTIONS] or difflib.get_close_matches(
            self.attribute, [*methods, *_PY_NAMES], n=1)
        suggestion = f"; did you mean {' or '.join(map(repr, hint))}?" if hint else ""
        return (f"{self.owner} has no attribute {self.attribute!r}{suggestion} "
                "(unlisted SVG attributes: element.set(name, value))")


class UnknownKeywordError(UnknownAttributeError, TypeError):
    """An unknown keyword argument (likely a typo); custom attributes go in ``attrs={...}``.

    Parameters
    ----------
    owner : str
        The class name of the element.
    name : str
        The keyword that was given.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.rect(0, 0, 1, 1, widht=3)
    ... except TypeError as error:
    ...     print(type(error).__name__)
    UnknownKeywordError
    """

    def __str__(self) -> str:
        hint = difflib.get_close_matches(self.attribute, _PY_NAMES, n=1)
        suggestion = f"; did you mean {hint[0]!r}?" if hint else ""
        return (f"{self.owner}() got an unknown attribute keyword {self.attribute!r}{suggestion} "
                "(custom attributes: attrs={...} or data_* keywords)")


@format_value.register(Element)
def _format_element(value: Element, precision: int = DEFAULT_PRECISION) -> str:
    return value.url.svg_value(precision)
