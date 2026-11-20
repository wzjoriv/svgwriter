import json

import numpy as np
import pytest

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


def test_an_eps_image_is_painted_in_document_order():
    doc = svg.Document(40, 20)
    doc.rect(0, 0, 40, 20, fill="white")
    doc.add(svg.Image(np.full((4, 4, 3), 0.0), 10, 5, 10, 10))
    doc.rect(15, 0, 25, 20, fill="red")
    text = svg.export.export(doc, "eps").decode()
    white, image, red = text.index("1 1 1 setrgbcolor"), text.index("colorimage"), text.index("1 0 0 setrgbcolor")
    assert white < image < red


def test_a_standalone_tikz_document_sets_fonts_that_match_the_measured_text():
    doc = svg.Document(100, 40)
    doc.text("Hello", x=10, y=30, font_size=12, font_family="Helvetica")
    text = svg.export.export(doc, "tikz", standalone=True)
    assert r"\usepackage{times}" in text.split(r"\begin{document}")[0]


def _picture_between_shapes():
    doc = svg.Document(40, 20)
    doc.rect(0, 0, 40, 20, fill="white")
    doc.add(svg.Image(np.full((4, 4, 3), 0.0), 10, 5, 10, 10))
    doc.rect(15, 0, 25, 20, fill="red")
    return doc


def test_a_pptx_picture_keeps_its_place_among_the_shapes():
    pytest.importorskip("pptx")
    back = svg.export.find_importer("pptx").function(svg.export.export(_picture_between_shapes(), "pptx"))
    assert [element.tag for element in back] == ["path", "image", "path"]


def test_an_excalidraw_image_keeps_its_place_among_the_shapes():
    scene = json.loads(svg.export.export(_picture_between_shapes(), "excalidraw"))
    assert [element["type"] for element in scene["elements"]] == ["line", "image", "line"]


def test_a_gradient_without_a_vector_form_becomes_its_average_colour():
    doc = svg.Document(40, 40)
    doc.circle(20, 20, 15, fill=svg.RadialGradient(svg.Stop(0, "white"), svg.Stop(1, "#000000")))
    element = json.loads(svg.export.export(doc, "excalidraw"))["elements"][0]
    assert element["backgroundColor"] == "#808080"


def test_a_pptx_equation_reads_back_centred_in_its_box_at_its_size():
    pytest.importorskip("pptx")
    doc = svg.Document(200, 100)
    formula = doc.add(svg.latex("x+1").translate(20, 30))
    box = formula.bounds()
    back = svg.export.find_importer("pptx").function(svg.export.export(doc, "pptx"))
    text = next(e for e in back.root.iter() if e.tag == "text")
    assert float(text.get("x")) == pytest.approx(box.x + box.width / 2, abs=0.5)
    assert box.y < float(text.get("y")) < box.y + box.height + 2
    assert float(text.get("font-size")) < 2 * box.height


def test_an_enlarged_image_has_no_dark_fringe_at_transparent_edges():
    pixels = np.zeros((8, 8, 4))
    pixels[4:] = 1
    doc = svg.Document(8, 8)
    doc.add(svg.Image(pixels, 0, 0, 8, 8))
    edge = doc.rasterize(scale=4)[12:20, 10]
    assert edge[edge[:, 3] > 0, :3].min() > 0.99
