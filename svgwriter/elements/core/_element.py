"""
The ``Element`` base class and the element registry.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias, TypeVar, Union, overload

from ..._internal._constants import DEFAULT_PRECISION
from ...attributes.names import KNOWN_ATTRIBUTES, UNSUPPORTED_ATTRIBUTES, svg_name
from ...attributes.values import format_value
from ._access import AttributeAccess
from ._categories import Category, ContentModel
from ._compose import Composable
from ._constants import INSTANCE_FIELDS, OPEN_PREFIXES
from ._construct import Construction
from ._display import Displayable
from ._errors import UnknownAttributeError, UnknownKeywordError
from ._query import Queryable
from ._tree import TreeEditing

if TYPE_CHECKING:
    from ..structure import Use

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
_ABSENT: Any = object()
Child: TypeAlias = Union["Element", str]


class Element(Construction, AttributeAccess, TreeEditing, Queryable, Displayable, Composable):
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
    svgwriter.elements.Container : Elements that hold children.

    Examples
    --------
    >>> import svgwriter as svg
    >>> el = svg.rect(0, 0, 10, 10, stroke_width=2)
    >>> el.tag, el.attributes["stroke-width"]
    ('rect', 2)
    """

    tag: ClassVar[str] = ""
    _auto_id: bool = False
    arranges_children: ClassVar[bool] = False
    """True for layout groups, which place their children before any child is measured."""
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
        self._assign(**extra)
        self.extend(children)

    def __getattr__(self, name: str) -> AttrValue:
        """Any SVG attribute by its Python name: ``el.stroke_width``, ``el.view_box``."""
        if name.startswith("__") or name.startswith("_") and not name.endswith("_") or name in INSTANCE_FIELDS:
            raise AttributeError(name)
        key = svg_name(name)
        if "attributes" in self.__dict__:
            value = self.get(key, _ABSENT)
            if value is not _ABSENT:
                return value
        if key in KNOWN_ATTRIBUTES:
            return None
        raise UnknownAttributeError(type(self).__name__, name, type(self))

    def __setattr__(self, name: str, value: AttrValue) -> None:
        if name in INSTANCE_FIELDS or name.startswith("_") and not name.endswith("_") or hasattr(type(self), name):
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
        from .._motion import Motion

        return Motion(self)

    @property
    def home(self) -> Element:
        """The element as it was when its first behavior was attached: a detached copy to start each frame from.

        A behavior that sets the state from :attr:`home` (``element.t = element.home.t``, then a relative move)
        computes every frame afresh, so the motion never drifts and frames can be drawn in any order.

        Returns
        -------
        Element
            The copy :meth:`Scene.attach <svgwriter.Scene.attach>` took.

        Raises
        ------
        ValueError
            If no behavior has been attached to this element.

        See Also
        --------
        svgwriter.preset.behavior : Write a behavior.

        Examples
        --------
        >>> import svgwriter as svg
        >>> class Hop(svg.Scene):
        ...     width, height, duration = 40, 40, 1.0
        ...     def build(self, doc):
        ...         self.dot = doc.circle(20, 30, 4).animate.hover(height=10).element
        >>> scene = Hop()
        >>> scene.dot.cy = 31
        >>> float(scene.dot.home.cy)
        30.0
        """
        home = self.__dict__.get("_home")
        if home is None:
            raise ValueError(f"<{self.tag}> has no home yet: it is recorded when a behavior is attached "
                             "(Scene.attach or element.animate.<behavior>)")
        return home  # type: ignore[no-any-return]

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
        from ...attributes.cascade import computed

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
            from ..structure import Use

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


@format_value.register(Element)
def _format_element(value: Element, precision: int = DEFAULT_PRECISION) -> str:
    return value.url.svg_value(precision)
