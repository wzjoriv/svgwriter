"""
Writing themes as TOML: the entries that differ from the theme they extend, edited into the theme's own
file when it came from one, so comments, layout, references and expressions survive.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import tomlkit

from ...errors import ThemeError
from ..attributes.style import Style
from ..color.color import Color, as_color
from ._constants import DEFAULT_THEME, FONT_TABLES
from ._resolve import resolve_value
from ._roles import DERIVED_PALETTE, STANDARD_ROLES
from ._toml_read import parse_document, read_value
from .fonts import Fonts, family_data

if TYPE_CHECKING:
    from .theme import Theme

__all__ = ["theme_to_toml"]

_MISSING: Final = object()
TomlValue = str | int | float | list[float]


def _color(color: Color) -> str | list[float]:
    exact = Color.parse(color.hex) == replace(color, icc=None)
    return color.hex if exact else list(color.rgba)


def _plain(value: object) -> TomlValue:
    if isinstance(value, Color):
        return _color(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (str, int, float)):
        return value
    if isinstance(value, Sequence):
        return _color(as_color(value))  # type: ignore[arg-type]
    return str(value)


def _same(first: object, second: object) -> bool:
    if first is second:
        return True
    if callable(first) or callable(second):
        return False
    return bool(first == second)


class _Table:
    """A table of the document that is created on its first write."""

    __slots__ = ("_make", "_table")

    def __init__(self, table: Any | None, make: Callable[[], Any]) -> None:
        self._table = table
        self._make = make

    def get(self, key: str) -> object:
        """The plain value the file holds for *key*, or None."""
        if self._table is None or key not in self._table:
            return None
        return self._table[key].unwrap()

    @property
    def exists(self) -> bool:
        """Whether the table is already in the document."""
        return self._table is not None

    def put(self, key: str, source: object, value: TomlValue, implicit: object = _MISSING) -> None:
        """Write *value* unless the file already holds *source* or leaving the key out gives *implicit*."""
        if self._table is not None and key in self._table:
            try:
                current = read_value(key, self._table[key].unwrap())
            except ThemeError:
                current = _MISSING
            if _same(current, source) or _same(current, value):
                return
        elif implicit is not _MISSING and _same(implicit, source):
            return
        if self._table is None:
            self._table = self._make()
        self._table[key] = value

    def child(self, key: str, *, super_table: bool = False) -> _Table:
        """The sub-table *key*, created (with its parent) on first write."""
        found = self._table.get(key) if self._table is not None else None

        def make() -> Any:
            if self._table is None:
                self._table = self._make()
            self._table[key] = tomlkit.table(is_super_table=super_table)
            return self._table[key]

        return _Table(found if isinstance(found, Mapping) else None, make)

    def role(self, name: str) -> _Table:
        """The table of role *name*, whether written ``[roles.a.b]`` or ``[roles."a.b"]``."""
        found = _find(self._table, name.split(".")) if self._table is not None else None
        return _Table(found, lambda: self.child(name)._create())

    def _create(self) -> Any:
        if self._table is None:
            self._table = self._make()
        return self._table


def _find(table: Mapping[str, Any], parts: list[str]) -> Any | None:
    if not parts:
        return table
    for count in range(len(parts), 0, -1):
        found = table.get(".".join(parts[:count]))
        if isinstance(found, Mapping):
            result = _find(found, parts[count:])
            if result is not None:
                return result
    return None


def _write_palette(theme: Theme, base: Theme | None, palette: _Table) -> None:
    base_sources = base.palette.sources if base is not None else DERIVED_PALETTE
    for key, source in theme.palette.sources.items():
        value = _plain(theme.palette[key] if callable(source) else source)
        palette.put(key, source, value, base_sources.get(key, _MISSING))


def _write_fonts(theme: Theme, base: Theme | None, fonts: _Table) -> None:
    base_fonts = base.fonts if base is not None else Fonts()
    for key in ("family", "monospace"):
        value = family_data(getattr(theme.fonts, key))
        if not _same_files(fonts, key, value):
            fonts.put(key, value, value, family_data(getattr(base_fonts, key)))
    for key in FONT_TABLES:
        table, base_table = getattr(theme.fonts, key), getattr(base_fonts, key)
        entries = fonts.child(key)
        for name, value in table.items():
            entries.put(name, value, value, base_table.get(name, _MISSING))


def _same_files(fonts: _Table, key: str, value: object) -> bool:
    """Whether the file already lists the same font files (as written, often relative) for *key*."""
    current = fonts.get(key)
    if not isinstance(value, list) or not isinstance(current, list):
        return False
    return [Path(str(item)).name for item in current] == [Path(item).name for item in value]


def _role_properties(theme: Theme, source: object) -> Style:
    return Style(source(theme) if callable(source) else source)  # type: ignore[arg-type]


def _write_roles(theme: Theme, base: Theme | None, roles: _Table) -> None:
    base_roles = base.roles if base is not None else STANDARD_ROLES
    for name, source in theme.roles.items():
        base_source = base_roles.get(name)
        table = roles.role(name)
        if source is base_source and not table.exists:
            continue
        base_properties = Style(base_source) if isinstance(base_source, Mapping) and not callable(source) else {}
        for prop, raw in _role_properties(theme, source).items():
            value = resolve_value(theme, f"roles.{name}.{prop}", raw) if callable(raw) else raw
            table.put(prop, raw, _plain(value), base_properties.get(prop, _MISSING))


def theme_to_toml(theme: Theme) -> str:
    """Write *theme* as TOML; see :meth:`Theme.to_toml`."""

    loaded = theme._document is not None
    document = parse_document(theme._document) if loaded else tomlkit.document()
    base = None
    if theme.extends is not None:
        try:
            from .theme import themes

            base = themes.get(theme.extends)
        except KeyError:
            raise ThemeError(f"extends: unknown theme {theme.extends!r}") from None
    root = _Table(document, lambda: document)
    root.put("name", theme.name, theme.name, base.name if loaded and base is not None else _MISSING)
    if theme.extends is not None:
        root.put("extends", theme.extends, theme.extends, DEFAULT_THEME if loaded else _MISSING)
    _write_palette(theme, base, root.child("palette"))
    _write_fonts(theme, base, root.child("fonts", super_table=True))
    _write_roles(theme, base, root.child("roles", super_table=True))
    return tomlkit.dumps(document)
