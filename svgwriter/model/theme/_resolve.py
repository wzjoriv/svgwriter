"""
Resolve role sources (mappings, functions, ``{section.name}`` references and expressions) into styles.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from ...errors import ThemeError
from ..attributes.style import Style
from ..color.color import Color
from ._constants import LENGTH_PROPERTIES, OPACITY_PROPERTIES, REFERENCE_RE, ROLE_NAME_RE
from ._expression import evaluate, is_expression

if TYPE_CHECKING:
    from .theme import RoleSource, Theme

__all__ = ["check_role_name", "resolve_role", "resolve_value"]


def check_role_name(name: str) -> str:
    """Return *name* if it is a valid role name (dotted lower-case words), else raise ThemeError."""
    if not isinstance(name, str) or ROLE_NAME_RE.fullmatch(name) is None:
        raise ThemeError(f"invalid role name {name!r}: use lower-case words joined by dots, like 'arrow.head'")
    return name


def _reference(theme: Theme, where: str, path: str) -> object:
    section, _, rest = path.partition(".")
    if section == "palette":
        if rest not in theme.palette:
            raise ThemeError(f"{where}: unknown reference {{{path}}}")
        return theme.palette[rest]
    if section == "fonts":
        try:
            return theme.fonts.lookup(rest)
        except ThemeError:
            raise ThemeError(f"{where}: unknown reference {{{path}}}") from None
    raise ThemeError(f"{where}: unknown reference {{{path}}}; use {{palette.name}} or {{fonts.name}}")


def resolve_value(theme: Theme, where: str, value: object) -> object:
    """Resolve one role property value: call a function, evaluate an expression or fill in references."""
    if callable(value):
        try:
            value = value(theme)
        except AttributeError as error:
            raise ThemeError(f"{where}: {error}") from None
    if not isinstance(value, str):
        return value
    whole = REFERENCE_RE.fullmatch(value.strip())
    if whole is not None:
        return _reference(theme, where, whole.group(1))
    if is_expression(value):
        result = evaluate(value, lambda path: _reference(theme, where, path), where)
        if isinstance(result, bool):
            raise ThemeError(f"{where}: a condition is not a CSS value; choose one with if(...)")
        return result
    return REFERENCE_RE.sub(lambda m: _text(_reference(theme, where, m.group(1))), value)


def _text(value: object) -> str:
    return value.svg_value() if isinstance(value, Color) else str(value)


def resolve_role(theme: Theme, name: str, source: RoleSource) -> Style:
    """Resolve one role's source against *theme* into a :class:`~svgwriter.model.attributes.Style`."""
    where = f"roles.{name}"
    if callable(source):
        try:
            source = source(theme)
        except AttributeError as error:
            raise ThemeError(f"{where}: {error}") from None
    if not isinstance(source, (Style, Mapping, str)):
        raise ThemeError(f"{where}: expected a mapping of CSS properties, got {type(source).__name__}")
    style = Style()
    for prop, raw in Style(source).items():
        value = resolve_value(theme, f"{where}.{prop}", raw)
        if isinstance(value, bool) or not isinstance(value, (str, int, float, Color)):
            raise ThemeError(f"{where}.{prop}: unsupported value {value!r}")
        if prop in LENGTH_PROPERTIES and isinstance(value, (int, float)):
            value = f"{value:g}px"
        style[prop] = value
        if isinstance(value, Color) and value.a < 1 and prop in OPACITY_PROPERTIES:
            style[OPACITY_PROPERTIES[prop]] = value.a
    return style
