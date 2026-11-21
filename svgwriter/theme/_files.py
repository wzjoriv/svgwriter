"""
Theme files: reading TOML into a theme and writing a theme as minimal TOML.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .._internal._typing import AnyPath
from ..color.color import Color
from ._constants import DEFAULT_THEME, FILE_FONT_KEYS, FILE_KEYS, TOML_BARE_KEY_RE
from .palette import ThemeError

if TYPE_CHECKING:
    from .theme import Theme

__all__ = ["ThemeFiles", "theme_from_toml", "theme_to_toml"]

def _parse(text: str) -> dict[str, Any]:
    try:
        import tomllib
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            raise ImportError("reading theme files needs tomli on Python < 3.11: pip install tomli") from None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ThemeError(f"invalid theme file: {error}") from None


def _literal(where: str, value: object) -> str | int | float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ThemeError(f"{where}: unsupported value {value!r}; use a string or a number")
    return value


def _table(where: str, value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ThemeError(f"{where}: expected a table")
    return dict(value)


def _roles(table: Mapping[str, Any], prefix: str = "") -> dict[str, dict[str, object]]:
    roles: dict[str, dict[str, object]] = {}
    properties: dict[str, object] = {}
    for key, value in table.items():
        if isinstance(value, Mapping):
            roles.update(_roles(value, f"{prefix}{key}."))
        else:
            properties[key] = _literal(f"roles.{prefix}{key}", value)
    if properties:
        if not prefix:
            raise ThemeError(f"roles: properties {sorted(properties)} need a role table such as [roles.box]")
        roles[prefix.rstrip(".")] = properties
    return roles


def theme_from_toml(text: str) -> Theme:
    """Build a theme from TOML text; see :meth:`Theme.from_toml`."""
    from .theme import Theme

    data = _parse(text)
    unknown = sorted(set(data) - FILE_KEYS)
    if unknown:
        raise ThemeError(f"unknown theme file keys {unknown}; expected {sorted(FILE_KEYS)}")
    base_name = _literal("extends", data.get("extends", DEFAULT_THEME))
    try:
        base = Theme.get(str(base_name))
    except KeyError:
        raise ThemeError(f"extends: unknown theme {base_name!r}") from None
    palette = {k: _literal(f"palette.{k}", v) for k, v in _table("palette", data.get("palette", {})).items()}
    fonts = _table("fonts", data.get("fonts", {}))
    unknown = sorted(set(fonts) - FILE_FONT_KEYS)
    if unknown:
        raise ThemeError(f"unknown font keys {unknown}; expected {sorted(FILE_FONT_KEYS)}")
    font_values = {k: (_table(f"fonts.{k}", v) if k in ("sizes", "weights") else _literal(f"fonts.{k}", v))
                   for k, v in fonts.items()}
    return base.replace(name=str(_literal("name", data.get("name", base.name))), palette=palette,
                        fonts=font_values, roles=_roles(_table("roles", data.get("roles", {}))))


def _key(name: str) -> str:
    return name if TOML_BARE_KEY_RE.fullmatch(name) else json.dumps(name)


def _value(value: object) -> str:
    if isinstance(value, Color):
        return json.dumps(value.hex)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return repr(value)
    return json.dumps(str(value), ensure_ascii=False)


def _section(header: str, entries: Mapping[str, object]) -> list[str]:
    return ["", f"[{header}]", *(f"{_key(k)} = {_value(v)}" for k, v in entries.items())]


def theme_to_toml(theme: Theme) -> str:
    """Write *theme* as TOML; see :meth:`Theme.to_toml`."""
    fonts = theme.fonts
    lines = [f"name = {_value(theme.name)}"]
    lines += _section("palette", dict(theme.palette))
    lines += _section("fonts", {"family": fonts.family, "monospace": fonts.monospace})
    lines += _section("fonts.sizes", dict(fonts.sizes))
    lines += _section("fonts.weights", dict(fonts.weights))
    for role in theme.roles:
        style = {k: v.svg_value() if isinstance(v, Color) else v for k, v in theme.style(role).items()}
        lines += _section(f"roles.{_key(role)}", style)
    return "\n".join(lines) + "\n"


class ThemeFiles:
    """Reading and writing TOML theme files; mixed into :class:`~svgwriter.Theme`."""

    __slots__ = ()

    @classmethod
    def load(cls, path: AnyPath) -> Theme:
        """Read a TOML theme file (see :meth:`from_toml`).

        Parameters
        ----------
        path : str or os.PathLike
            The file.

        Returns
        -------
        Theme
            The theme.

        Examples
        --------
        >>> import svgwriter as svg, tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "night.toml"
        ...     svg.Theme.get("dark").replace(name="night").save(path)
        ...     svg.Theme.load(path).name
        'night'
        """
        return cls.from_toml(Path(os.fspath(path)).read_text(encoding="utf-8"))

    def save(self, path: AnyPath) -> None:
        """Write the theme as TOML (see :meth:`to_toml`).

        Parameters
        ----------
        path : str or os.PathLike
            The file to write.

        Examples
        --------
        >>> import svgwriter as svg, tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "mono.toml"
        ...     svg.Theme.get("mono").save(path)
        ...     path.read_text(encoding="utf-8").startswith('name = "mono"')
        True
        """
        Path(os.fspath(path)).write_text(self.to_toml(), encoding="utf-8")

    @classmethod
    def from_toml(cls, text: str) -> Theme:
        """Build a theme from TOML text.

        The file is a variant of ``extends`` (a registered name, default ``"light"``) with
        ``name``, ``[palette]``, ``[fonts]`` (with ``[fonts.sizes]`` and ``[fonts.weights]``) and
        ``[roles.<name>]`` tables. Values are literals or ``{palette.name}`` /
        ``{fonts.sizes.name}`` references; nothing is executed.

        Parameters
        ----------
        text : str
            The TOML document.

        Returns
        -------
        Theme
            The theme.

        Raises
        ------
        ThemeError
            On unknown keys, unsupported values, unknown references or cycles.

        Examples
        --------
        >>> import svgwriter as svg
        >>> theme = svg.Theme.from_toml('''
        ... name = "night"
        ... extends = "dark"
        ... [palette]
        ... primary = "#ff8800"
        ... accent = "{palette.primary}"
        ... [roles.badge]
        ... fill = "{palette.accent}"
        ... ''')
        >>> theme.style("badge")["fill"].hex
        '#ff8800'
        """
        return theme_from_toml(text)

    def to_toml(self) -> str:
        """The theme as TOML text with every value resolved to a literal.

        Returns
        -------
        str
            The TOML document; :meth:`from_toml` reads it back to an equal theme.

        Notes
        -----
        Functions and references are written as the values they resolve to, so the file is a
        snapshot: derived entries no longer follow their sources once read back.

        Examples
        --------
        >>> import svgwriter as svg
        >>> paper = svg.Theme.get("paper")
        >>> svg.Theme.from_toml(paper.to_toml()) == paper
        True
        """
        return theme_to_toml(self)  # type: ignore[arg-type]
