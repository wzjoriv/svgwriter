"""Every format that both writes and reads gives back a drawing that renders like the original."""

import numpy as np
import pytest

import svgwriter as svg

IMPORTER = {"svgz": "svg", "png": "image", "jpeg": "image", "webp": "image", "bmp": "image", "gif": "image",
            "ppm": "pnm"}
EXACT = {"svg": 0.001, "svgz": 0.001, "pdf": 0.01, "tikz": 0.01, "eps": 0.02, "excalidraw": 0.02, "pptx": 0.02}
SCALED = {"pptx"}
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
    if fmt == "pptx":
        pytest.importorskip("pptx")
    data = svg.export.export(original, fmt)
    back = svg.export.find_importer(IMPORTER.get(fmt, fmt)).function(data.encode() if isinstance(data, str) else data)
    if fmt not in SCALED:
        back.root.set("viewBox", original.root.get("viewBox"))
    back.root.set("width", SIZE[0])
    back.root.set("height", SIZE[1])
    assert np.abs(_render(back) - _render(original)).mean() < tolerance


def _gradients():
    doc = svg.Document(*SIZE)
    linear = svg.LinearGradient(svg.Stop(0, "red"), svg.Stop(0.5, "gold"), svg.Stop(1, "blue"))
    doc.rect(5, 5, 50, 50, fill=linear).rotate(15)
    doc.circle(80, 30, 18, fill=svg.RadialGradient(svg.Stop(0, "white"), svg.Stop(1, "navy")))
    doc.rect(0, 0, 1, 1, fill="masooma")
    return doc


def test_gradients_become_native_shadings():
    eps = svg.export.export(_gradients(), "eps")
    assert eps.count(b"shfill") == 2 and b"%%LanguageLevel: 3" in eps and b"0 0.502 0 setrgbcolor" in eps
    tikz = svg.export.export(_gradients(), "tikz")
    assert "shading=axis" in tikz and "shading=radial" in tikz and "middle color" in tikz


def test_eps_draws_images_in_place():
    doc = svg.Document(*SIZE)
    doc.add(svg.Image(np.ones((2, 2, 3)) * [1, 0, 0], 10, 10, 20, 20)).rotate(30)
    eps = svg.export.export(doc, "eps")
    assert eps.count(b"colorimage") == 1 and b"ff0000ff0000" in eps


@pytest.mark.parametrize("fmt", ["eps", "tikz"])
def test_patterns_survive_vector_export(fmt):
    dots = svg.Pattern(svg.circle(5, 5, 3, fill="crimson"), width=10, height=10, pattern_units="userSpaceOnUse")
    doc = svg.Document(*SIZE)
    doc.circle(30, 30, 25, fill=dots, stroke="black")
    data = svg.export.export(doc, fmt)
    back = svg.export.find_importer(fmt).function(data.encode() if isinstance(data, str) else data)
    back.root.set("viewBox", doc.root.get("viewBox"))
    back.root.set("width", SIZE[0])
    back.root.set("height", SIZE[1])
    assert np.abs(_render(back) - _render(doc)).mean() < 0.05
