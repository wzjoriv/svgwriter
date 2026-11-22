"""
``Palette``: named color roles, each a literal, a reference, an expression or a function of the palette.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import TypeAlias

from ...errors import ThemeError
from ..color.color import Color, ColorLike, as_color
from ._constants import MAX_REFERENCE_DEPTH, REFERENCE_RE
from ._expression import evaluate, is_expression

__all__ = ["Palette", "PaletteSource"]


PaletteSource: TypeAlias = "ColorLike | Callable[[Palette], ColorLike]"


class Palette(Mapping[str, Color]):
    """Immutable color roles, resolved once from literals, references, expressions and functions.

    Parameters
    ----------
    sources : mapping of str to color or str or callable
        Each role's source: a color (``"#0f766e"``, ``"navy"``, a :class:`~svgwriter.Color`), a
        reference to another role written ``"{palette.name}"``, an expression marked
        with a leading ``=`` such as ``"=lighten({palette.primary}, 0.2)"`` (see the Themes guide), or a function that receives
        this palette and returns a color (``lambda p: p.foreground.mix(p.background, 0.3)``).

    Raises
    ------
    ThemeError
        If a reference names a missing role, references form a cycle or nest too deeply, an
        expression is malformed, or a value is not a color.

    See Also
    --------
    Theme : Combines a palette with fonts and role styles.

    Notes
    -----
    Sources are kept, so :meth:`replace` derives again: replacing ``foreground`` also changes
    every role computed from it. Roles read as attributes (``palette.primary``) or keys.

    Examples
    --------
    >>> from svgwriter.model.theme import Palette
    >>> p = Palette({"ink": "#000000", "paper": "white", "line": lambda p: p.ink.mix(p.paper, 0.5)})
    >>> p.line.hex
    '#808080'
    >>> p.replace(ink="#ff0000").line.hex
    '#ff8080'
    >>> Palette({"ink": "navy", "label": "=readable({palette.ink})"}).label.hex
    '#ffffff'
    """

    __slots__ = ("_resolving", "_sources", "_values")

    def __init__(self, sources: Mapping[str, PaletteSource]) -> None:
        self._sources: dict[str, PaletteSource] = dict(sources)
        self._values: dict[str, Color] = {}
        self._resolving: list[str] = []
        for name in self._sources:
            self._resolve(name)

    def _resolve(self, name: str) -> Color:
        if name in self._values:
            return self._values[name]
        if name in self._resolving:
            cycle = " -> ".join(f"palette.{n}" for n in [*self._resolving[self._resolving.index(name):], name])
            raise ThemeError(f"reference cycle: {cycle}")
        if name not in self._sources:
            raise ThemeError(f"unknown palette role {name!r}")
        if len(self._resolving) >= MAX_REFERENCE_DEPTH:
            raise ThemeError(f"palette.{name}: references nest deeper than {MAX_REFERENCE_DEPTH} levels")
        self._resolving.append(name)
        try:
            self._values[name] = self._evaluate(name, self._sources[name])
        finally:
            self._resolving.pop()
        return self._values[name]

    def _reference(self, name: str, path: str) -> Color:
        section, _, key = path.partition(".")
        if section != "palette" or key not in self._sources:
            raise ThemeError(f"palette.{name}: unknown reference {{{path}}}")
        return self._resolve(key)

    def _evaluate(self, name: str, source: PaletteSource) -> Color:
        if callable(source):
            try:
                return as_color(source(self))
            except AttributeError as error:
                raise ThemeError(f"palette.{name}: {error}") from None
        if isinstance(source, str) and (whole := REFERENCE_RE.fullmatch(source.strip())) is not None:
            return self._reference(name, whole.group(1))
        if isinstance(source, str) and is_expression(source):
            source = evaluate(source, lambda path: self._reference(name, path), f"palette.{name}")  # type: ignore[assignment]
            if isinstance(source, bool) or not isinstance(source, (str, Color)):
                raise ThemeError(f"palette.{name}: expected a color, got {source!r}")
        try:
            return as_color(source)
        except (TypeError, ValueError) as error:
            raise ThemeError(f"palette.{name}: {error}") from None

    @property
    def sources(self) -> Mapping[str, PaletteSource]:
        """Each role's source as given: literals, references and functions.

        Examples
        --------
        >>> from svgwriter.model.theme import Palette
        >>> Palette({"a": "red", "b": "{palette.a}"}).sources["b"]
        '{palette.a}'
        """
        return dict(self._sources)

    def replace(self, **sources: PaletteSource) -> Palette:
        """A new palette with some sources replaced or added; derived roles follow.

        Parameters
        ----------
        **sources : color or str or callable
            The roles to replace or add, by name.

        Returns
        -------
        Palette
            The merged palette.

        Examples
        --------
        >>> from svgwriter.model.theme import Palette
        >>> Palette({"a": "red", "b": "{palette.a}"}).replace(a="blue").b.hex
        '#0000ff'
        """
        return Palette({**self._sources, **sources})

    def __getitem__(self, name: str) -> Color:
        return self._resolve(name)

    def __getattr__(self, name: str) -> Color:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except ThemeError as error:
            if name in self._sources:
                raise
            raise AttributeError(str(error)) from None

    def __contains__(self, name: object) -> bool:
        return name in self._sources

    def __iter__(self) -> Iterator[str]:
        return iter(self._sources)

    def __len__(self) -> int:
        return len(self._sources)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Palette):
            return NotImplemented
        return {k: v.hex for k, v in self.items()} == {k: v.hex for k, v in other.items()}

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return "Palette({" + ", ".join(f"{k!r}: {v.hex!r}" for k, v in self.items()) + "})"
