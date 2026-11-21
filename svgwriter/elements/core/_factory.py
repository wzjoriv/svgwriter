"""
``ElementFactory``: ``doc.circle(...)``-style shortcuts, typed from the element constructors.
"""

from __future__ import annotations

import functools
import importlib
import inspect
from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Concatenate, Final, Generic, ParamSpec, TypeVar

if TYPE_CHECKING:
    from ..filters import Filter
    from ..paint import ClipPath, LinearGradient, Marker, Mask, Pattern, RadialGradient
    from ..shapes import Circle, Ellipse, Line, Path, Polygon, Polyline, Rect
    from ..structure import A, Group, Image, Switch, Symbol, Use
    from ..text import Text
    from ._element import Element

__all__ = ["ElementFactory"]

E = TypeVar("E", bound="Element")
P = ParamSpec("P")
R = TypeVar("R")

PLACED: Final = {
    "rect": ("shapes", "Rect"), "circle": ("shapes", "Circle"), "ellipse": ("shapes", "Ellipse"),
    "line": ("shapes", "Line"), "polyline": ("shapes", "Polyline"), "polygon": ("shapes", "Polygon"),
    "path": ("shapes", "Path"), "text": ("text", "Text"), "group": ("structure", "Group"),
    "link": ("structure", "A"), "switch": ("structure", "Switch"), "use": ("structure", "Use"),
    "image": ("structure", "Image"),
}
DEFINED: Final = {
    "linear_gradient": ("paint", "LinearGradient"), "radial_gradient": ("paint", "RadialGradient"),
    "pattern": ("paint", "Pattern"), "clip_path": ("paint", "ClipPath"), "mask": ("paint", "Mask"),
    "marker": ("paint", "Marker"), "filter": ("filters", "Filter"), "symbol": ("structure", "Symbol"),
}


class _Shortcut(Generic[P, R]):
    """A method that builds one element class, adds it and returns it; resolved on first use."""

    def __init__(self, module: str, name: str, *, define: bool) -> None:
        self.module, self.name, self.define = module, name, define
        self._function: Callable[..., Any] | None = None

    def __set_name__(self, owner: type, attribute: str) -> None:
        self.attribute = attribute

    def _build(self) -> Callable[..., Any]:
        cls = getattr(importlib.import_module(f"..{self.module}", __package__), self.name)
        place = "_define" if self.define else "_place"
        where = "into ``<defs>`` (with an id)" if self.define else "at the insertion point"

        @functools.wraps(cls)
        def shortcut(owner: Any, *args: Any, **kwargs: Any) -> Any:
            return getattr(owner, place)(cls(*args, **kwargs))

        shortcut.__name__ = shortcut.__qualname__ = self.attribute
        shortcut.__doc__ = (f"Add a :class:`~svgwriter.{self.name}` built from the same arguments, {where}.\n\n"
                            f"Returns the new element; see :class:`~svgwriter.{self.name}` for the parameters.")
        signature = inspect.signature(cls)
        shortcut.__signature__ = signature.replace(  # type: ignore[attr-defined]
            parameters=[inspect.Parameter("self", inspect.Parameter.POSITIONAL_ONLY), *signature.parameters.values()],
            return_annotation=self.name)
        return shortcut

    def __get__(self, owner: object, owner_type: type | None = None) -> Any:
        if self._function is None:
            self._function = self._build()
        return self._function if owner is None else self._function.__get__(owner, owner_type)


if TYPE_CHECKING:
    def _typed(cls: Callable[P, R]) -> Callable[Concatenate[Any, P], R]: ...


class ElementFactory:
    """Shortcut methods shared by :class:`~svgwriter.Document` and containers.

    ``doc.rect(...)`` takes exactly the arguments of :class:`~svgwriter.Rect`,
    adds the new element and returns it, and so on for every element class:
    shapes, text, groups, links, ``<switch>``, ``<use>`` and images go to the
    insertion point; gradients, patterns, clip paths, masks, markers, filters
    and symbols go into ``<defs>`` with an id. Editors and type checkers see
    each constructor's own signature.

    See Also
    --------
    svgwriter.elements.GraphicsContainer : Containers that use these shortcuts.

    Examples
    --------
    >>> from svgwriter import Document
    >>> doc = Document(100, 100)
    >>> sky = doc.linear_gradient(x2=0, y2=1)
    >>> doc.rect(0, 0, 100, 100, fill=sky).get("fill") == sky.url
    True
    >>> sky.parent is doc.defs
    True
    >>> [doc.circle(5, 5, 2).tag, doc.text("hi", x=1, y=9).tag, doc.group().tag]
    ['circle', 'text', 'g']
    """

    __slots__ = ()

    @abstractmethod
    def _place(self, element: E) -> E:
        """Add *element* at the insertion point and return it."""

    @abstractmethod
    def _define(self, element: E) -> E:
        """Add *element* to the applicable ``<defs>`` and return it."""

    if TYPE_CHECKING:
        rect = _typed(Rect)
        circle = _typed(Circle)
        ellipse = _typed(Ellipse)
        line = _typed(Line)
        polyline = _typed(Polyline)
        polygon = _typed(Polygon)
        path = _typed(Path)
        text = _typed(Text)
        group = _typed(Group)
        link = _typed(A)
        switch = _typed(Switch)
        use = _typed(Use)
        image = _typed(Image)
        linear_gradient = _typed(LinearGradient)
        radial_gradient = _typed(RadialGradient)
        pattern = _typed(Pattern)
        clip_path = _typed(ClipPath)
        mask = _typed(Mask)
        marker = _typed(Marker)
        filter = _typed(Filter)
        symbol = _typed(Symbol)
    else:
        for _name, (_module, _cls) in PLACED.items():
            locals()[_name] = _Shortcut(_module, _cls, define=False)
        for _name, (_module, _cls) in DEFINED.items():
            locals()[_name] = _Shortcut(_module, _cls, define=True)
        del _name, _module, _cls
