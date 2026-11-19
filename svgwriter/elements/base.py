"""The ``Element`` base class and the element registry."""

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
_XML_NAME_RE: Final = re.compile(r"^[A-Za-z_][\w.\-]*$")


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
        The element id.
    attrs : mapping, optional
        Extra attributes given by their SVG names.
    **extra
        Any other attribute, Python spelling.
    """

    tag: ClassVar[str] = ""
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
        raise UnknownAttributeError(type(self).__name__, name)

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
        """Return the registered class for *tag*."""
        return cls._registry.get(tag)

    @classmethod
    def registered(cls, category: Category | None = None) -> dict[str, type[Element]]:
        """Registered element classes, optionally filtered by category."""
        return {
            tag: klass for tag, klass in cls._registry.items()
            if category is None or klass.category is category
        }

    @classmethod
    def from_attributes(cls: type[E], attributes: Mapping[str, str]) -> E:
        """Build an instance from raw SVG attributes, bypassing ``__init__``."""
        obj = cls.__new__(cls)
        Element.__init__(obj)
        obj.attributes.update(attributes)
        return obj

    @property
    def id(self) -> str | None:
        value = self.attributes.get("id")
        return None if value is None else str(value)

    @id.setter
    def id(self, value: str | None) -> None:
        if value is None:
            self.attributes.pop("id", None)
            return
        if not _XML_NAME_RE.match(value):
            raise ValueError(f"invalid id: {value!r}")
        self.attributes = {"id": value, **{k: v for k, v in self.attributes.items() if k != "id"}}

    def ensure_id(self) -> ElementId:
        """Return the id, assigning a generated one if needed."""
        if self.id is None:
            self.id = next_id(self.tag or "el")
        return ElementId(self.id or "")

    @property
    def ref(self) -> FuncIRI:
        """``url(#id)`` for this element, assigning an id if needed."""
        return FuncIRI("#" + self.ensure_id(), self)

    @property
    def href(self) -> IRI:
        """``#id`` for this element, assigning an id if needed."""
        return IRI("#" + self.ensure_id(), self)

    @chainable
    def set(self, name: str, value: AttrValue) -> None:
        """Set one attribute; ``None`` removes it.

        Attributes in other namespaces use Clark notation: ``"{uri}name"``.
        """
        key = name if name.startswith("{") else svg_name(name)
        if key in UNSUPPORTED_ATTRIBUTES:
            raise ValueError(
                f"{key!r} is a scripting/browser attribute; svgwriter writes static graphics and does not support it"
            )
        if value is None:
            self.attributes.pop(key, None)
            return
        if key in COLOR_ATTRIBUTES and not isinstance(value, (str, Element)) and not hasattr(value, "svg_value"):
            value = as_color(value)
        if isinstance(value, Color) and value.a < 1.0 and key in COLOR_ATTRIBUTES:
            if key not in COLOR_OPACITY:
                raise ValueError(f"{key} has no opacity in SVG 1.1; use an opaque color")
            self.attributes[COLOR_OPACITY[key]] = value.a
            value = value.opaque
        if isinstance(value, Element):
            value = value.href if key in HREF_ATTRIBUTES else value.ref
        elif isinstance(value, FuncIRI) and key in HREF_ATTRIBUTES:
            value = IRI(value.target, value.element)
        self.attributes[key] = value
        if getattr(value, "element", None) is not None:
            self._define_references(self)

    @chainable
    def update(self, attributes: Mapping[str, AttrValue] | None = None, /, **kwargs: AttrValue) -> None:
        """Set several attributes; ``None`` values are skipped."""
        for name, value in {**(attributes or {}), **kwargs}.items():
            if value is not None:
                self.set(name, value)

    @overload
    def get(self, name: str) -> AttrValue | None: ...
    @overload
    def get(self, name: str, default: T) -> AttrValue | T: ...
    def get(self, name: str, default: object = None) -> object:
        return self.attributes.get(svg_name(name), default)

    def has(self, name: str) -> bool:
        return svg_name(name) in self.attributes

    def discard(self, name: str) -> None:
        self.attributes.pop(svg_name(name), None)

    def append(self, child: C) -> C:
        """Append a child element or text node and return it."""
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
            for value in list(element.attributes.values()):
                target = getattr(value, "element", None)
                if target is not None and target.parent is None and target is not root:
                    root.defs().append(target)  # type: ignore[attr-defined]

    def extend(self, children: Iterable[Child]) -> None:
        for child in children:
            self.append(child)

    def insert(self, index: int, child: C) -> C:
        self.append(child)
        self.children.insert(index, self.children.pop())
        return child

    def remove(self, child: Child) -> None:
        self.children.remove(child)
        if isinstance(child, Element):
            child.parent = None

    def clear(self) -> None:
        for child in self.children:
            if isinstance(child, Element):
                child.parent = None
        self.children.clear()

    @property
    def text(self) -> str:
        """Concatenated direct text children."""
        return "".join(c for c in self.children if isinstance(c, str))

    @text.setter
    def text(self, value: str) -> None:
        self.children = [c for c in self.children if not isinstance(c, str)]
        if value:
            self.insert(0, value)

    def computed(self, name: str, default: object = None) -> object:
        """The value SVG would use for property *name* (SVG spelling or Python spelling).

        Looks at the inline ``style``, matching ``<style>`` rules, the
        presentation attribute, then ancestors for inherited properties.

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
        """Depth-first walk over this element and its descendants."""
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
        """First descendant (or self) matching a tag or class."""
        return next(iter(self.find_all(match)), None)

    @overload
    def find_all(self, match: type[E]) -> list[E]: ...
    @overload
    def find_all(self, match: str) -> list[Element]: ...
    def find_all(self, match: type[Element] | str) -> list[Element]:
        if isinstance(match, str):
            return list(self.iter(match))
        return [e for e in self.iter() if isinstance(e, match)]

    def get_element_by_id(self, element_id: str) -> Element | None:
        return next((e for e in self.iter() if e.id == element_id), None)

    def root(self) -> Element:
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

        Examples
        --------
        >>> import svgwriter as svg
        >>> star = svg.circle(0, 0, 5, id="dot")
        >>> star.clone().id, star.clone(linked=True).tag
        ('dot', 'use')

        Notes
        -----
        A linked clone needs the original in the same document: placed
        anywhere, or unplaced, in which case it moves into ``<defs>`` when
        the ``<use>`` joins the document. ``copy.copy`` and ``copy.deepcopy``
        both behave like ``clone()``.
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
        """Serialize; see :class:`svgwriter.io.SerializeOptions`."""
        from ..io.writer import to_string

        return to_string(self, **options)

    def save(self, target: AnyPath | TextSink, **options: Any) -> None:
        """Write to a path or text stream."""
        from ..io.writer import write

        write(self, target, **options)

    def _repr_svg_(self) -> str:
        return self.to_string(xml_declaration=False)

    def __str__(self) -> str:
        return self.to_string(xml_declaration=False, pretty=False)

    def __repr__(self) -> str:
        shown = " ".join(f"{k}={format_value(v)!r}" for k, v in list(self.attributes.items())[:3])
        return f"<{type(self).__name__} {self.tag}{' ' + shown if shown else ''}>"


_INSTANCE_FIELDS: Final = frozenset({"attributes", "children", "parent"})
_PY_NAMES: Final = sorted({py_name(n) for n in KNOWN_ATTRIBUTES})


class UnknownAttributeError(AttributeError):
    """An attribute that is neither a Python member nor a known SVG attribute.

    The "did you mean" suggestion is computed only when the message is shown,
    so ``getattr(element, name, default)`` stays cheap.
    """

    def __init__(self, owner: str, name: str) -> None:
        super().__init__(name)
        self.owner = owner
        self.attribute = name

    def __str__(self) -> str:
        hint = difflib.get_close_matches(self.attribute, _PY_NAMES, n=1)
        suggestion = f"; did you mean {hint[0]!r}?" if hint else ""
        return (f"{self.owner} has no attribute {self.attribute!r}{suggestion} "
                "(unlisted SVG attributes: element.set(name, value))")


@format_value.register(Element)
def _format_element(value: Element, precision: int = DEFAULT_PRECISION) -> str:
    return value.ref.svg_value(precision)
