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
