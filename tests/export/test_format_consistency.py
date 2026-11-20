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


def test_a_pdf_colour_after_a_pattern_fill_paints_solid_again():
    doc = svg.Document(100, 50)
    dots = doc.define(svg.Pattern(svg.circle(5, 5, 3, fill="blue"), width=10, height=10, pattern_units="userSpaceOnUse"))
    doc.rect(0, 0, 40, 40, fill=dots, stroke="blue")
    doc.circle(70, 20, 15, fill="red")
    back = svg.export.find_importer("pdf").function(svg.export.export(doc, "pdf"))
    assert str(list(back)[-1].get("fill")) == "#ff0000"
