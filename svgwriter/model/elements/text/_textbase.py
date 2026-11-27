"""
Shared ``<text>``/``<tspan>`` bases: per-character positioning and ``textLength``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeAlias

from ...._internal._typing import LengthAdjust
from ...units.lengths import LengthLike
from ..core import Child, Element

if TYPE_CHECKING:
    from ._text import TextDecoration

__all__ = ["Coordinates"]

Coordinates: TypeAlias = LengthLike | Sequence[LengthLike]


def _coords(value: Coordinates | None) -> Any:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return value


class _TextPositioning(Element):
    """``x``, ``y``, ``dx``, ``dy`` and ``rotate``, each a number or list, and ``decoration`` for ``text-decoration``."""

    def __init__(
        self,
        *args: Child,
        x: Coordinates | None = None,
        y: Coordinates | None = None,
        dx: Coordinates | None = None,
        dy: Coordinates | None = None,
        rotate: float | Sequence[float] | None = None,
        decoration: TextDecoration | str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._assign(x=_coords(x), y=_coords(y), dx=_coords(dx), dy=_coords(dy), rotate=_coords(rotate))
        if decoration is not None:
            self.set("text-decoration", decoration)

    @property
    def text_content(self) -> str:
        """All characters, ``tspan`` runs included; assigning replaces the runs and resets per-character positions.

        ``x`` and ``y`` keep their first value; ``dx``, ``dy`` and ``rotate``
        lists are dropped because they no longer match the characters.

        Examples
        --------
        >>> import svgwriter as svg
        >>> t = svg.text("Hello world", x=[0, 5, 10], y=20)
        >>> t[6:].fill = "red"
        >>> t.text_content = "Bye"
        >>> str(t)
        '<text x="0" y="20">Bye</text>'
        """
        return Element.text_content.fget(self)  # type: ignore[attr-defined,no-any-return]

    @text_content.setter
    def text_content(self, value: str) -> None:
        from ._textlayout import number_list

        Element.text_content.fset(self, value)  # type: ignore[attr-defined]
        for name in ("x", "y"):
            values = number_list(self.get(name))
            self.set(name, values[0] if values else None)
        for name in ("dx", "dy", "rotate"):
            self.discard(name)


class _TextLength(Element):
    def __init__(
        self,
        *args: Child,
        text_length: LengthLike | None = None,
        length_adjust: LengthAdjust | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._assign(text_length=text_length, length_adjust=length_adjust)


def _all_text(element: Element) -> str:
    return "".join(c if isinstance(c, str) else _all_text(c) for c in element.children)
