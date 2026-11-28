import pytest

import svgwriter as svg

pptx = pytest.importorskip("pptx")
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402


def _deck(tmp_path, build):
    deck = pptx.Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    build(slide)
    path = tmp_path / "deck.pptx"
    deck.save(path)
    return path


def test_common_presets_are_drawn(tmp_path):
    def build(slide):
        for index, kind in enumerate((MSO_SHAPE.RIGHT_ARROW, MSO_SHAPE.ISOSCELES_TRIANGLE, MSO_SHAPE.DIAMOND,
                                      MSO_SHAPE.HEXAGON, MSO_SHAPE.STAR_5_POINT, MSO_SHAPE.CHEVRON)):
            slide.shapes.add_shape(kind, Inches(0.2 + index * 1.5), Inches(1), Inches(1.2), Inches(1))

    doc = svg.Document.open(_deck(tmp_path, build))
    assert len([e for e in doc.root.iter() if e.tag == "path"]) == 6


def test_unknown_presets_warn_and_keep_their_box(tmp_path):
    def build(slide):
        slide.shapes.add_shape(MSO_SHAPE.CLOUD, Inches(1), Inches(1), Inches(2), Inches(1))

    with pytest.warns(UserWarning, match="'cloud' is not supported yet"):
        doc = svg.Document.open(_deck(tmp_path, build))
    assert any(e.tag == "path" for e in doc.root.iter())


def test_shape_text_follows_its_alignment_and_anchor(tmp_path):
    def build(slide):
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(4), Inches(2))
        box.text_frame.text = "Centred"
        box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        box.text_frame.paragraphs[0].runs[0].font.size = Pt(20)
        box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    doc = svg.Document.open(_deck(tmp_path, build))
    text = next(e for e in doc.root.iter() if e.tag == "text")
    assert text.get("text-anchor") == "middle"
    centre_x, centre_y = (1 + 2) * 96, (1 + 1) * 96
    assert abs(float(text.get("x")) - centre_x) < 2 and abs(float(text.get("y")) - centre_y) < 20
