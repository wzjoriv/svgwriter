import io
import zipfile

import numpy as np
import pytest
from lxml import etree

import svgwriter as svg

docx = pytest.importorskip("docx")
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
READ = svg.export.find_importer("docx").function


def _saved(word):
    buffer = io.BytesIO()
    word.save(buffer)
    return buffer.getvalue()


def _png(color="red"):
    doc = svg.Document(30, 15)
    doc.rect(0, 0, 30, 15, fill=color)
    return io.BytesIO(doc.export("png"))


def _texts(doc):
    return [t for t in doc.root.iter() if t.tag == "text"]


def test_paragraphs_headings_and_styled_runs():
    word = docx.Document()
    word.add_heading("Report", 0)
    word.add_heading("Part", 2)
    paragraph = word.add_paragraph("plain ")
    paragraph.add_run("bold").bold = True
    run = paragraph.add_run(" red")
    run.italic, run.underline = True, True
    run.font.color.rgb = docx.shared.RGBColor(255, 0, 0)
    run.font.size = docx.shared.Pt(15)
    texts = _texts(READ(_saved(word)))
    assert [t.text_content for t in texts] == ["Report", "Part", "plain bold red"]
    assert (texts[0].get("font-size"), texts[1].get("font-size")) == (32, 26)
    assert texts[0].get("font-weight") == "bold"
    bold, red = texts[2].children[1], texts[2].children[2]
    assert bold.get("font-weight") == "bold"
    assert red.get("font-style") == "italic" and red.get("text-decoration") == "underline"
    assert red.get("fill") == "#ff0000" and red.get("font-size") == pytest.approx(20)
    assert [t.get("y") for t in texts] == sorted(t.get("y") for t in texts)


def test_bullets_numbers_and_levels():
    word = docx.Document()
    word.add_paragraph("dot", style="List Bullet")
    word.add_paragraph("first", style="List Number")
    word.add_paragraph("second", style="List Number")
    word.add_paragraph("break")
    word.add_paragraph("again", style="List Number")
    texts = [t.text_content for t in _texts(READ(_saved(word)))]
    assert texts == ["• dot", "1. first", "2. second", "break", "1. again"]


def test_pictures_keep_their_place_in_the_flow():
    word = docx.Document()
    word.add_paragraph("above")
    word.add_picture(_png(), width=docx.shared.Emu(9525 * 60))
    word.add_paragraph("below")
    group = READ(_saved(word))[0]
    tags = [e.tag for e in group]
    assert tags == ["text", "image", "text"]
    above, image, below = group
    assert above.get("y") < image.get("y") and image.get("y") + image.height < below.get("y")
    assert image.width == pytest.approx(60, abs=0.1) and image.rgba()[0, 0, 0] > 0.9


def test_a_line_break_starts_a_new_line():
    word = docx.Document()
    paragraph = word.add_paragraph("one")
    paragraph.add_run().add_break()
    paragraph.add_run("two")
    assert [t.text_content for t in _texts(READ(_saved(word)))] == ["one", "two"]


def _drawing():
    doc = svg.Document(200, 100)
    doc.rect(10, 10, 80, 40, fill=(1, 0, 0, 0.5), stroke="navy", stroke_width=4)
    doc.circle(150, 30, 20, fill=svg.LinearGradient.horizontal("red", "blue"))
    doc.add(svg.Image(np.ones((4, 4, 3)) * [0, 1, 0], 120, 60, 40, 30))
    doc.text("Hi & bye", x=20, y=90, font_size=14, fill="purple", font_weight="bold")
    return doc


def test_export_writes_native_shapes_pictures_and_text_boxes():
    data = svg.export.export(_drawing(), "docx")
    body = etree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"))
    names = [a.find(f"{WP}docPr").get("name").split()[0] for a in body.iter(f"{WP}anchor")]
    assert names == ["Shape", "Shape", "Picture", "Text"]
    assert not list(body.iter(f"{WP}inline"))
    assert body.find(".//{*}gradFill") is not None and body.find(".//{*}custDash") is None
    docx.Document(io.BytesIO(data))


def test_export_round_trip():
    back = READ(svg.export.export(_drawing(), "docx"))
    paths = [e for e in back if e.tag == "path"]
    assert len(paths) == 2 and paths[0].get("stroke-width") == pytest.approx(4)
    assert paths[0].get("fill-opacity") == pytest.approx(0.5, abs=0.01)
    image = next(e for e in back if e.tag == "image")
    assert (image.x, image.y, image.width, image.height) == pytest.approx((125, 60, 30, 30), abs=0.5)
    text = _texts(back)[0]
    assert text.text_content == "Hi & bye" and text.children[0].get("font-weight") == "bold"
    assert text.get("y") + text.parent.transform.f == pytest.approx(90, abs=0.5)


def test_rotated_text_turns_its_box():
    doc = svg.Document(100, 100)
    doc.text("turn", x=50, y=50, font_size=12).rotate(90, about=(50, 50))
    body = etree.fromstring(zipfile.ZipFile(io.BytesIO(svg.export.export(doc, "docx"))).read("word/document.xml"))
    assert body.find(".//{*}xfrm").get("rot") == str(90 * 60000)
