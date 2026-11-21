"""
Inline CSS declarations and small style sheets.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from typing import TypeAlias

from ..._internal._constants import DEFAULT_PRECISION
from .names import PRESENTATION_ATTRIBUTES, svg_name

__all__ = ["Style", "StyleLike", "StyleSheet"]


def _css_name(name: str) -> str:
    return svg_name(name) if "_" in name else name


class Style(MutableMapping[str, object]):
    """Ordered CSS declarations for a ``style`` attribute.

    Keys accept Python spelling (``stroke_width``) or CSS spelling
    (``stroke-width``). Assigning ``None`` removes a declaration. It is a
    mutable mapping that keeps insertion order.

    Parameters
    ----------
    declarations : Style or mapping or str, optional
        Initial declarations, or CSS text such as ``"fill:red;stroke:blue"``. Defaults to None.
    **properties
        More declarations as keywords.

    See Also
    --------
    StyleSheet : Builder for ``<style>`` element text.

    Examples
    --------
    >>> from svgwriter.model.attributes import Style
    >>> str(Style(fill="red", stroke_width=2))
    'fill:red;stroke-width:2'
    """

    def __init__(self, declarations: StyleLike | None = None, /, **properties: object) -> None:
        self._data: dict[str, object] = {}
        if isinstance(declarations, str):
            self.update(self.parse(declarations))
        elif declarations is not None:
            self.update(declarations)
        self.update(properties)

    @staticmethod
    def parse(text: str) -> dict[str, str]:
        """Split CSS declaration text into a dict.

        Parameters
        ----------
        text : str
            Declarations separated by semicolons, such as ``"a:b; c:d"``.

        Returns
        -------
        dict of str to str
            Property names mapped to values; malformed items are skipped.

        Examples
        --------
        >>> from svgwriter.model.attributes import Style
        >>> Style.parse("a:b; c:d")
        {'a': 'b', 'c': 'd'}
        """
        result: dict[str, str] = {}
        for chunk in text.split(";"):
            name, sep, value = chunk.partition(":")
            if sep and name.strip():
                result[name.strip()] = value.strip()
        return result

    def presentation_only(self) -> Style:
        """Return the declarations that are SVG presentation properties.

        Returns
        -------
        Style
            A new style holding only presentation properties such as ``fill``.

        Examples
        --------
        >>> from svgwriter.model.attributes import Style
        >>> str(Style(fill="red", custom="x").presentation_only())
        'fill:red'
        """
        return Style({k: v for k, v in self._data.items() if k in PRESENTATION_ATTRIBUTES})

    def __getitem__(self, key: str) -> object:
        return self._data[_css_name(key)]

    def __setitem__(self, key: str, value: object) -> None:
        if value is None:
            self._data.pop(_css_name(key), None)
        else:
            self._data[_css_name(key)] = value

    def __delitem__(self, key: str) -> None:
        del self._data[_css_name(key)]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"Style({self._data!r})"

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize as the text of a ``style`` attribute.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places for numbers. Defaults to the library default precision.

        Returns
        -------
        str
            Declarations joined by semicolons.

        Examples
        --------
        >>> from svgwriter.model.attributes import Style
        >>> Style(fill="red", stroke_width=1.5).svg_value()
        'fill:red;stroke-width:1.5'
        """
        from .values import format_value

        return ";".join(f"{k}:{format_value(v, precision)}" for k, v in self._data.items())

    def __str__(self) -> str:
        return self.svg_value()


StyleLike: TypeAlias = Style | Mapping[str, object] | str


class StyleSheet:
    """Builder for the text of a ``<style>`` element.

    Parameters
    ----------
    rules : iterable of tuple, optional
        Initial ``(selector, declarations)`` pairs. Defaults to none.

    See Also
    --------
    Style : A single declaration block.

    Examples
    --------
    >>> from svgwriter.model.attributes import StyleSheet
    >>> sheet = StyleSheet().rule(".accent", fill="tomato")
    >>> sheet.css()
    '.accent { fill:tomato }'
    """

    def __init__(self, rules: Iterable[tuple[str, StyleLike]] = ()) -> None:
        self._rules: list[tuple[str, Style]] = [(s, Style(d)) for s, d in rules]

    def rule(self, selector: str, declarations: StyleLike | None = None, /, **properties: object) -> StyleSheet:
        """Append a rule.

        Parameters
        ----------
        selector : str
            CSS selector.
        declarations : Style or mapping or str, optional
            Declarations as accepted by `Style`. Defaults to None.
        **properties
            More declarations as keywords.

        Returns
        -------
        StyleSheet
            The sheet itself, for chaining.

        Examples
        --------
        >>> from svgwriter.model.attributes import StyleSheet
        >>> StyleSheet().rule("rect", {"stroke": "blue"}).rule(".a", fill="red").css(" ")
        'rect { stroke:blue } .a { fill:red }'
        """
        self._rules.append((selector, Style(declarations, **properties)))
        return self

    def __iter__(self) -> Iterator[tuple[str, Style]]:
        return iter(self._rules)

    def __len__(self) -> int:
        return len(self._rules)

    def css(self, separator: str = "\n") -> str:
        """Render the sheet as CSS text.

        Parameters
        ----------
        separator : str, optional
            Text placed between rules. Defaults to a newline.

        Returns
        -------
        str
            One ``selector { declarations }`` entry per rule.

        Examples
        --------
        >>> from svgwriter.model.attributes import StyleSheet
        >>> StyleSheet().rule(".a", fill="red").css()
        '.a { fill:red }'
        """
        return separator.join(f"{selector} {{ {style} }}" for selector, style in self._rules)

    def __str__(self) -> str:
        return self.css()
