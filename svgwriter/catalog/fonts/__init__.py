"""Fonts from drawings: letters, icons, kerning, OpenType and web-font export.

:class:`FontBuilder` collects glyphs drawn with svgwriter shapes and writes
``.otf``, ``.ttf``, ``.woff`` and ``.woff2`` files, an icon stylesheet and a
cheatsheet. Compiling needs the ``fonts`` extra (``pip install 'pysvgwriter[fonts]'``).

Examples
--------
>>> import svgwriter as svg
>>> fb = svg.fonts.FontBuilder(family="Shapes")
>>> fb.icon("square", svg.rect(0, 0, 10, 10))
'\ue000'
"""

from __future__ import annotations

from .builder import FontBuilder

__all__ = ["FontBuilder"]
