"""Composite shapes (star, gear, heart, callout, wave, ...), parametric stars and arcs, and the ``drawing`` decorator.

Plain elements are built with the classes or their lowercase aliases (``svg.circle``); this module adds
what the element classes do not provide.
"""

from __future__ import annotations

from ..._internal._presets import SHAPES
from ._drawing import drawing
from ._functions import dashed_line, dot, outline
from ._lines import grid, spiral, wave
from ._parametric import Arc, Star, parametric
from ._shapes import arrow, gear, regular_polygon, star
from ._symbols import callout, cross, heart

__all__ = [
    "Arc",
    "Star",
    "arrow",
    "callout",
    "cross",
    "dashed_line",
    "dot",
    "drawing",
    "gear",
    "grid",
    "heart",
    "outline",
    "parametric",
    "regular_polygon",
    "spiral",
    "star",
    "wave",
]

SHAPES.seal()
