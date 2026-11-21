from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg

BLUE = (0.0, 0.0, 1.0, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)


def draw(body: str, style: str = "") -> np.ndarray:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        f'<style>{style}</style><defs><marker id="m" markerWidth="2" markerHeight="2" fill="blue">'
        '<rect width="50" height="50"/></marker></defs>' + body + "</svg>")
    return doc.rasterize(background="white")


@pytest.mark.parametrize("overflow, painted", [("hidden", False), ("visible", True)])
def test_content_is_clipped_to_the_marker_viewport(overflow: str, painted: bool) -> None:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><defs>'
        f'<marker id="m" markerWidth="2" markerHeight="2" overflow="{overflow}" fill="blue">'
        '<rect width="50" height="50"/></marker></defs>'
        '<path d="M10 10 L10 10" stroke-width="10" marker-end="url(#m)"/></svg>')
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[15, 15], BLUE, atol=0.02)
    assert np.allclose(pixels[45, 45], BLUE if painted else WHITE, atol=0.02)


def test_content_inherits_from_the_marker() -> None:
    pixels = draw('<path d="M10 10 L50 10" fill="red" marker-start="url(#m)"/>')
    assert np.allclose(pixels[11, 11], BLUE, atol=0.02)


def test_marker_properties_inherit_and_come_from_css() -> None:
    pixels = draw('<g marker-start="url(#m)"><path d="M10 10 L50 10"/></g><path class="end" d="M10 60 L50 60"/>',
                  ".end { marker-end: url(#m) }")
    assert np.allclose(pixels[11, 11], BLUE, atol=0.02)
    assert np.allclose(pixels[61, 51], BLUE, atol=0.02)


def test_marker_shorthand_applies_from_css_but_not_as_attribute() -> None:
    pixels = draw('<path class="all" d="M10 10 L50 10"/><path marker="url(#m)" d="M10 60 L50 60"/>',
                  ".all { marker: url(#m) }")
    assert np.allclose(pixels[11, 51], BLUE, atol=0.02)
    assert np.allclose(pixels[61, 51], WHITE, atol=0.02)
