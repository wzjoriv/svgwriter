"""Themes: palettes, fonts and role styles that documents apply as CSS classes.

A :class:`Theme` is immutable. Elements opt in with ``element.as_role("box")``; a document writes one
``<style>`` rule per role it uses, so the SVG stays portable and can be restyled by swapping the sheet.
Built-in themes are ``light`` (the default), ``dark``, ``paper``, ``print``, ``mono``, ``noir``, ``brutalist``,
``dracula``, ``alucard``, ``one-dark`` and ``one-light``.
"""

from __future__ import annotations

from ._builtin import register_builtins
from ._errors import ThemeError
from .fonts import Fonts
from .palette import Palette, PaletteSource
from .theme import THEMES, RoleSource, Theme

__all__ = ["THEMES", "Fonts", "Palette", "PaletteSource", "RoleSource", "Theme", "ThemeError"]

register_builtins()
