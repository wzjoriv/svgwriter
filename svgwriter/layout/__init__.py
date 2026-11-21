"""Layout groups: stacks and grids that place their children by size.

:class:`VStack`, :class:`HStack` and :class:`Grid` are ``<g>`` elements that move their
children (and stretch rects, images and nested layouts) from their measured boxes, with gaps,
padding, alignment and an optional background. Changing a child, the gap or the size re-lays
the group out the next time it is measured or written. The output is plain groups with
transforms, so every exporter keeps the layout.

Examples
--------
>>> import svgwriter as svg
>>> keys = [svg.VStack(svg.text(k, font_size=14), padding=8, align="center", background="box")
...         for k in "789456123"]
>>> card = svg.VStack(svg.text("Calculator", font_size=16), svg.Grid(*keys, columns=3, gap=6),
...                   gap=10, padding=12, background="surface")
>>> doc = svg.Document()
>>> doc += card
>>> card.bounds().width > 0
True
"""

from __future__ import annotations

from ._frame import Frame, settle
from ._grid import Grid
from ._stack import HStack, Spacer, Stack, VStack

__all__ = ["Frame", "Grid", "HStack", "Spacer", "Stack", "VStack", "settle"]
