"""
Methods of the style and presentation attribute groups: classes, ``style`` and CSS round trips.
"""

from __future__ import annotations

from typing import Any

from ..._internal._registry import chainable
from ...attributes.names import PRESENTATION_ATTRIBUTES
from ...attributes.style import Style, StyleLike

__all__ = ["PresentationMethods", "StyleMethods"]


class PresentationMethods:
    """Presentation attributes as a dict and as CSS; mixed into :class:`~svgwriter.elements.PresentationAttributes`."""

    __slots__ = ()

    def presentation(self) -> dict[str, Any]:
        """Presentation attributes currently set as XML attributes.

        Returns
        -------
        dict
            Attribute values keyed by SVG name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.rect(0, 0, 1, 1, fill="red").presentation()
        {'fill': 'red'}
        """
        return {k: v for k, v in self.attributes.items() if k in PRESENTATION_ATTRIBUTES}

    @chainable
    def to_css(self) -> None:
        """Move presentation attributes into the ``style`` attribute.

        See Also
        --------
        from_css : The reverse.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1, fill="red")
        >>> _ = r.to_css()
        >>> r.has("fill"), r.style["fill"]
        (False, 'red')
        """
        style = self.style
        for name, value in self.presentation().items():
            style[name] = value
            del self.attributes[name]
        self.style = style

    @chainable
    def from_css(self) -> None:
        """Move presentation properties out of ``style`` into attributes.

        See Also
        --------
        to_css : The reverse.

        Examples
        --------
        >>> import svgwriter as svg
        >>> r = svg.rect(0, 0, 1, 1, style="fill: red")
        >>> _ = r.from_css()
        >>> r.get("fill")
        'red'
        """
        style = self.style
        for name, value in style.presentation_only().items():
            self.attributes[name] = value
            del style[name]
        self.style = style


class StyleMethods:
    """Classes and inline style; mixed into :class:`~svgwriter.elements.StyleAttributes`."""

    __slots__ = ()

    @property
    def classes(self) -> list[str]:
        """The class names in the ``class`` attribute.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.group(class_="a b").classes
        ['a', 'b']
        """
        return str(self.attributes.get("class", "")).split()

    @chainable
    def add_class(self, *names: str) -> None:
        """Add class names that are not already present.

        Parameters
        ----------
        *names : str
            The class names to add.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(class_="a")
        >>> _ = g.add_class("a", "b")
        >>> g.classes
        ['a', 'b']
        """
        merged = self.classes + [n for n in names if n not in self.classes]
        self.attributes["class"] = " ".join(merged)

    @property
    def style(self) -> Style:
        """A copy of the ``style`` attribute; assign to change it.

        Examples
        --------
        >>> import svgwriter as svg
        >>> g = svg.group(style="fill: red")
        >>> g.style["fill"]
        'red'
        """
        raw = self.attributes.get("style")
        return Style(raw) if raw is not None else Style()

    @style.setter
    def style(self, value: StyleLike | None) -> None:
        style = Style(value) if value is not None else Style()
        if style:
            self.attributes["style"] = style
        else:
            self.attributes.pop("style", None)
