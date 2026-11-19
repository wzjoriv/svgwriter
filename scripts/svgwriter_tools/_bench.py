"""Timing the hot paths: building, writing, parsing, geometry, rendering and exporting."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

import svgwriter as svg

REPEAT = 3


@dataclass
class Timing:
    name: str
    seconds: float
    per_item_us: float


def _best(function: Callable[[], object], repeat: int = REPEAT) -> float:
    best = float("inf")
    for _ in range(repeat):
        start = time.perf_counter()
        function()
        best = min(best, time.perf_counter() - start)
    return best


def _scene(count: int) -> svg.Document:
    doc = svg.Document(1000, 1000)
    rng = np.random.default_rng(0)
    for x, y, r in rng.uniform(0, 1000, (count, 3)):
        doc.circle(x, y, r / 50, fill="teal")
    return doc


def run(count: int = 100_000, figures: int = 100) -> list[Timing]:
    """Time each scenario; *count* elements for the tree benchmarks, *figures* small documents for batches."""
    timings: list[Timing] = []

    def record(name: str, function: Callable[[], object], items: int) -> None:
        seconds = _best(function)
        timings.append(Timing(name, seconds, 1e6 * seconds / max(items, 1)))

    record(f"build {count} circles", lambda: _scene(count), count)
    doc = _scene(count)
    record("transform every circle", lambda: [c.translate(1, 0).rotate(5) for c in doc], count)
    text = doc.to_string()
    record("write SVG", doc.to_string, count)
    record("parse SVG", lambda: svg.Document.from_string(text), count)
    record("bounds of every circle", lambda: [c.bounds() for c in doc], count)
    record("content bounds (auto-size)", doc.content_bounds, count)
    small = _scene(1000)
    record("rasterize 1000 circles", small.rasterize, 1000)
    record("export PDF 1000 circles", lambda: small.export("pdf"), 1000)
    record("export EPS 1000 circles", lambda: small.export("eps"), 1000)
    record("union of 200 circles", lambda: list(_scene(200))[0].union(*list(_scene(200))[1:]), 200)
    paragraph = svg.Text("The quick brown fox jumps over the lazy dog. " * 20, x=0, y=20)
    record("layout 900-character text", paragraph.layout, len(paragraph))
    docs = [_scene(50) for _ in range(figures)]
    record(f"rasterize {figures} figures", lambda: [d.rasterize() for d in docs], figures)
    record(f"PNG export {figures} figures", lambda: [d.export("png") for d in docs], figures)
    return timings
