import numpy as np

import svgwriter as svg


def _arrow_document():
    doc = svg.Document(100, 40)
    doc.rect(0, 0, 100, 40, fill="white")
    doc.path("M10 20 L80 20", fill="none", stroke="red", stroke_width=2, marker_end=svg.builder.arrow_marker("red", 6))
    return doc


def test_a_parsed_marker_with_a_view_box_renders_like_the_original():
    doc = _arrow_document()
    again = svg.Document.from_string(doc.to_string())
    assert np.abs(again.rasterize() - doc.rasterize()).max() < 1e-6
