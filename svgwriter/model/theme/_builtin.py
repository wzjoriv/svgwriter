"""
The built-in themes: light (the default), dark, paper, print, mono, noir, brutalist, dracula, alucard,
one-dark and one-light.
"""

from __future__ import annotations

from ._constants import BUILTIN_THEMES
from .fonts import Fonts
from .theme import Theme, themes

__all__ = ["register_builtins"]


def register_builtins() -> None:
    """Register every built-in theme: its palette, font changes and role changes over the standard ones."""
    for name, spec in BUILTIN_THEMES.items():
        base = Theme(name, spec["palette"], Fonts().replace(**spec.get("fonts", {})))
        themes.add_builtin(name, base.replace(roles=spec.get("roles", {})))
