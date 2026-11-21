from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg


def test_filter_on_a_mask_is_ignored() -> None:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><defs>'
        '<filter id="f" filterUnits="userSpaceOnUse" x="0" y="0" width="100" height="100">'
        '<feOffset dx="50" dy="50"/></filter>'
        '<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="100" filter="url(#f)">'
        '<rect width="50" height="50" fill="white"/></mask></defs>'
        '<rect width="100" height="100" fill="lime" mask="url(#m)"/></svg>')
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[25, 25], (0, 1, 0, 1), atol=0.02)
    assert np.allclose(pixels[75, 75], (1, 1, 1, 1), atol=0.02)


def test_visible_child_of_a_hidden_group_is_drawn() -> None:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><g visibility="hidden">'
        '<rect width="50" height="100" fill="red"/><rect x="50" width="50" height="100" fill="lime" '
        'visibility="visible"/></g></svg>')
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[50, 25], (1, 1, 1, 1), atol=0.02)
    assert np.allclose(pixels[50, 75], (0, 1, 0, 1), atol=0.02)


def test_elements_from_other_namespaces_are_not_drawn() -> None:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><g xmlns:s="http://www.w3.org/2000/svg">'
        '<circle xmlns="http://example.org/other" cx="50" cy="50" r="50" fill="red"/>'
        '<s:rect width="50" height="50" fill="lime"/></g></svg>')
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[25, 25], (0, 1, 0, 1), atol=0.02)
    assert np.allclose(pixels[75, 75], (1, 1, 1, 1), atol=0.02)


@pytest.mark.parametrize("overflow, outside", [("hidden", (1, 1, 1, 1)), ("visible", (0, 1, 0, 1))])
def test_nested_svg_clips_to_its_viewport(overflow: str, outside: tuple) -> None:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        f'<svg x="20" y="20" width="40" height="40" viewBox="0 0 20 20" overflow="{overflow}">'
        '<rect x="-10" y="-10" width="40" height="40" fill="lime"/></svg></svg>')
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[40, 40], (0, 1, 0, 1), atol=0.02)
    assert np.allclose(pixels[10, 10], outside, atol=0.02)


def test_sliced_image_is_clipped_to_its_viewport() -> None:
    doc = svg.Document(100, 100)
    doc.add(svg.Image(np.ones((10, 20, 3)) * [0, 1, 0], 25, 25, 50, 50, preserve_aspect_ratio="xMidYMid slice"))
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[50, 30], (0, 1, 0, 1), atol=0.02)
    assert np.allclose(pixels[50, 10], (1, 1, 1, 1), atol=0.02)
