"""Batches: thousands of similar shapes made, moved, styled and written as numpy columns.

Each factory takes scalars or arrays that broadcast together (numpy rules) and returns a
:class:`Batch`, a ``<g>`` whose items are ordinary SVG elements in the output. While compact, the
batch stores one column per attribute, so making, transforming, restyling and writing 100,000
items costs a few numpy operations instead of 100,000 Python objects. ``batch[i]``, iteration and
``batch.animate`` turn the items into real elements when they are needed one by one.

Examples
--------
>>> import numpy as np
>>> import svgwriter as svg
>>> rng = np.random.default_rng(1)
>>> x, y = rng.normal(50, 15, (2, 1000))
>>> doc = svg.Document(100, 100)
>>> dots = doc.add(svg.batch.points(x, y, 1.5, fill=svg.batch.colormap("plasma", y), opacity=0.7))
>>> _ = dots.rotate(rng.uniform(0, 90, 1000)).translate(0, 2)
>>> doc.to_string().count("<circle")
1000
"""

from __future__ import annotations

from ._batch import Batch
from ._factories import circles, instances, lines, points, polylines, rects, texts
from ._motion import BatchMotion
from ._paint import colormap, colormaps

__all__ = [
    "Batch",
    "BatchMotion",
    "circles",
    "colormap",
    "colormaps",
    "instances",
    "lines",
    "points",
    "polylines",
    "rects",
    "texts",
]
