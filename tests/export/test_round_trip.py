"""Every format that both writes and reads gives back a drawing that renders like the original."""

import numpy as np
import pytest

import svgwriter as svg

IMPORTER = {"svgz": "svg", "png": "image", "jpeg": "image", "webp": "image", "bmp": "image", "gif": "image",
            "ppm": "pnm"}
EXACT = {"svg": 0.001, "svgz": 0.001, "pdf": 0.01, "tikz": 0.01, "eps": 0.02, "excalidraw": 0.02}
RASTER = {"png": 0.02, "jpeg": 0.03, "webp": 0.02, "bmp": 0.02, "gif": 0.03, "ppm": 0.02}
SIZE = (100, 60)


def _sample() -> svg.Document:
    doc = svg.Document(*SIZE)
    doc.rect(5, 5, 40, 25, fill="teal")
    doc.circle(70, 20, 12, fill="none", stroke="crimson", stroke_width=3)
    doc.path(fill="none", stroke="navy", stroke_width=2).move_to(5, 50).curve_to(30, 30, 60, 70, 95, 45)
    doc.polygon([(50, 35), (60, 55), (40, 55)], fill=(1, 0.6, 0, 0.5))
    return doc


def _render(doc: svg.Document) -> np.ndarray:
    return doc.rasterize(size=SIZE, background="white")[..., :3]


@pytest.mark.parametrize(("fmt", "tolerance"), sorted({**EXACT, **RASTER}.items()))
def test_round_trip_renders_like_the_original(fmt: str, tolerance: float) -> None:
    original = _sample()
    data = svg.export.export(original, fmt)
    back = svg.export.find_importer(IMPORTER.get(fmt, fmt)).function(data.encode() if isinstance(data, str) else data)
    back.root.set("viewBox", original.root.get("viewBox"))
    back.root.set("width", SIZE[0])
    back.root.set("height", SIZE[1])
    assert np.abs(_render(back) - _render(original)).mean() < tolerance
