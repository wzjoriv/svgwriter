from __future__ import annotations

import numpy as np

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
