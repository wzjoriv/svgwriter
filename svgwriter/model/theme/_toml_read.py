"""
Reading TOML theme files: checking their keys and turning their values into theme sources.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit
from tomlkit.exceptions import TOMLKitError

from ...errors import ThemeError
from ..color.color import Color
from ._constants import (
    ARRAY_CHANNELS,
    ARRAY_INTEGER_MAX,
    DEFAULT_THEME,
    FILE_FONT_KEYS,
    FILE_KEYS,
    FONT_TABLES,
    MAX_MAGNITUDE,
)

if TYPE_CHECKING:
    from .theme import Theme

__all__ = ["parse_document", "read_roles", "read_value", "theme_from_toml"]


def parse_document(text: str) -> tomlkit.TOMLDocument:
    """Parse TOML *text*, keeping its comments and layout; raise ThemeError if it is not valid TOML."""
    try:
        return tomlkit.parse(text)
    except TOMLKitError as error:
        raise ThemeError(f"invalid theme file: {error}") from None


def _number(where: str, value: float) -> float:
    if not math.isfinite(value):
        raise ThemeError(f"{where}: {value} is not a finite number")
    if abs(value) > MAX_MAGNITUDE:
        raise ThemeError(f"{where}: number too large; the limit is {MAX_MAGNITUDE:g}")
    return value


def _array_color(where: str, values: list[Any]) -> Color:
    if len(values) not in ARRAY_CHANNELS or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                                for v in values):
        raise ThemeError(f"{where}: a color array holds 3 or 4 numbers")
    if all(isinstance(v, int) for v in values):
        if any(not 0 <= v <= ARRAY_INTEGER_MAX for v in values):
            raise ThemeError(f"{where}: integer channels run from 0 to {ARRAY_INTEGER_MAX}")
        return Color.from_uint8(*values)
    if any(isinstance(v, int) for v in values):
        raise ThemeError(f"{where}: use all floats (0 to 1) or all integers (0 to 255), not a mix")
    try:
        return Color(*values)
    except ValueError:
        raise ThemeError(f"{where}: float channels run from 0 to 1") from None


def read_value(where: str, value: object) -> str | float | Color:
    """One palette or role value from a file: text, a finite number or a color array."""
    if isinstance(value, list):
        return _array_color(where, value)
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(where, value)
    raise ThemeError(f"{where}: unsupported value {value!r}; use text, a number or a color array")


def _text(where: str, value: object) -> str:
    if not isinstance(value, str):
        raise ThemeError(f"{where}: expected text, got {value!r}")
    return value


def _table(where: str, value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ThemeError(f"{where}: expected a table")
    return dict(value)


def _family(where: str, value: object, folder: Path | None) -> object:
    """A family name, or a list of font files (relative to the theme file) loaded as a typeface."""
    if not isinstance(value, list):
        return _text(where, value)
    from ...ops.typeface import Typeface

    paths = [(folder or Path()) / _text(where, item) for item in value]
    try:
        return Typeface.from_files(*paths)
    except (OSError, ValueError) as error:
        raise ThemeError(f"{where}: {error}") from None


def _fonts(table: Mapping[str, Any], folder: Path | None = None) -> dict[str, Any]:
    unknown = sorted(set(table) - FILE_FONT_KEYS)
    if unknown:
        raise ThemeError(f"unknown font keys {unknown}; expected {sorted(FILE_FONT_KEYS)}")
    fonts: dict[str, Any] = {}
    for key, value in table.items():
        if key in FONT_TABLES:
            entries = _table(f"fonts.{key}", value)
            fonts[key] = {k: read_value(f"fonts.{key}.{k}", v) for k, v in entries.items()}
            for name, entry in fonts[key].items():
                if not isinstance(entry, (int, float)):
                    raise ThemeError(f"fonts.{key}.{name}: expected a number, got {entry!r}")
        else:
            fonts[key] = _family(f"fonts.{key}", value, folder)
    return fonts


def read_roles(table: Mapping[str, Any], prefix: str = "") -> dict[str, dict[str, object]]:
    """The ``[roles]`` table as role name to properties; nested tables give dotted names."""
    roles: dict[str, dict[str, object]] = {}
    properties: dict[str, object] = {}
    for key, value in table.items():
        if isinstance(value, Mapping):
            roles.update(read_roles(value, f"{prefix}{key}."))
        else:
            properties[key] = read_value(f"roles.{prefix}{key}", value)
    if properties:
        if not prefix:
            raise ThemeError(f"roles: properties {sorted(properties)} need a role table such as [roles.box]")
        roles[prefix.rstrip(".")] = properties
    return roles


def theme_from_toml(text: str, folder: Path | None = None) -> Theme:
    """Build a theme from TOML text; see :meth:`Theme.from_toml`. Font files resolve against *folder*."""
    from .theme import themes

    data = parse_document(text).unwrap()
    unknown = sorted(set(data) - FILE_KEYS)
    if unknown:
        raise ThemeError(f"unknown theme file keys {unknown}; expected {sorted(FILE_KEYS)}")
    base_name = _text("extends", data.get("extends", DEFAULT_THEME))
    try:
        base = themes.get(base_name)
    except KeyError:
        raise ThemeError(f"extends: unknown theme {base_name!r}") from None
    palette = {k: read_value(f"palette.{k}", v) for k, v in _table("palette", data.get("palette", {})).items()}
    theme = base.replace(name=_text("name", data.get("name", base.name)), palette=palette,
                         fonts=_fonts(_table("fonts", data.get("fonts", {})), folder),
                         roles=read_roles(_table("roles", data.get("roles", {}))))
    return theme._from_file(base_name, text)
