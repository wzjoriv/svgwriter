import io
import sys

import numpy as np
import pytest

import svgwriter as svg

pptx = pytest.importorskip("pptx")


def _doc():
    doc = svg.Document(200, 100)
    doc.rect(10, 10, 80, 40, fill=(1, 0, 0, 0.5), stroke="navy", stroke_width=4)
    doc.add(svg.Image(np.ones((4, 4, 3)) * [0, 1, 0], 120, 10, 40, 40))
    return doc


def test_pptx_shapes_keep_paint_alpha_and_pictures():
    deck = pptx.Presentation(io.BytesIO(svg.export.export(_doc(), "pptx")))
    shapes = list(deck.slides[0].shapes)
    kinds = sorted(type(s).__name__ for s in shapes)
    assert kinds == ["Picture", "Shape"]
    back = svg.formats.reader("pptx").read(svg.export.export(_doc(), "pptx"))
    path = next(e for e in back if e.tag == "path")
    assert path.get("fill-opacity") == pytest.approx(0.5) and path.get("stroke-width") == pytest.approx(4)
    assert any(e.tag == "image" for e in back)


def test_pptx_reads_text_boxes_and_presets():
    deck = pptx.Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    box = slide.shapes.add_textbox(pptx.util.Emu(9525 * 10), pptx.util.Emu(9525 * 10), pptx.util.Emu(9525 * 200),
                                   pptx.util.Emu(9525 * 40))
    box.text_frame.text = "Hello"
    oval = slide.shapes.add_shape(pptx.enum.shapes.MSO_SHAPE.OVAL, 0, 0, pptx.util.Emu(9525 * 50),
                                  pptx.util.Emu(9525 * 30))
    oval.fill.solid()
    oval.fill.fore_color.rgb = pptx.dml.color.RGBColor(0, 128, 0)
    buffer = io.BytesIO()
    deck.save(buffer)
    back = svg.formats.reader("pptx").read(buffer.getvalue())
    tags = [e.tag for e in back.root.iter() if e.tag in ("text", "path")]
    assert "text" in tags and "path" in tags
    with pytest.raises(IndexError, match="slides"):
        svg.formats.reader("pptx").read(buffer.getvalue(), slide=3)


def test_excel_holds_a_picture():
    data = svg.export.export(_doc(), "xlsx")
    assert data[:2] == b"PK" and len(data) > 1000


def test_missing_library_explains_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "docx", None)
    with pytest.raises(ImportError, match=r"svgwriter\[office\]"):
        svg.export.export(_doc(), "docx")
