"""
``element.interact.<name>(...)``: the interaction presets registered with ``@svg.preset.interaction``.
"""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING, Any

from ..._internal._constants import SUGGESTIONS
from ..._internal._presets import INTERACTIONS

if TYPE_CHECKING:
    from .core import Element

__all__ = ["Interactions"]


class Interactions:
    """The interaction presets of one element; each call applies one and returns the element.

    Parameters
    ----------
    element : Element
        The element to make interactive.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(width=60, height=30)
    >>> key = doc.rect(5, 5, 50, 20, id="key").interact.button()
    >>> "#key:hover" in doc.to_string() and "key.mousedown" in doc.to_string()
    True
    """

    __slots__ = ("element",)

    def __init__(self, element: Element) -> None:
        self.element = element

    def __getattr__(self, name: str) -> Any:
        if name not in INTERACTIONS.list():
            close = difflib.get_close_matches(name, INTERACTIONS.list(), n=SUGGESTIONS)
            hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
            raise AttributeError(f"no interaction preset {name!r}{hint} (@svg.preset.interaction adds one)",
                                 name=name, obj=self)
        function = INTERACTIONS.get(name)

        def apply(**options: Any) -> Element:
            function(self.element, **options)
            return self.element

        apply.__doc__ = function.__doc__
        return apply

    def __dir__(self) -> list[str]:
        return sorted({*super().__dir__(), *INTERACTIONS.list()})
