"""
The built-in themes: light (the default), dark, paper, print and mono.
"""

from __future__ import annotations

from ._constants import BUILTIN_PALETTES
from .theme import THEMES, Theme

__all__ = ["register_builtins"]


def register_builtins() -> None:
    """Register one theme per built-in palette, all sharing the standard roles and fonts."""
    for name, palette in BUILTIN_PALETTES.items():
        THEMES.add(name, Theme(name, palette))
