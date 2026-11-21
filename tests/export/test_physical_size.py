from __future__ import annotations

import io
import re

import pytest

import svgwriter as svg
from svgwriter.export import find_importer

A4_PT = (595.28, 841.89)
A4_EMU = (7560000, 10692000)
LETTER_PT = (612, 792)
PX_PER_MM = 96 / 25.4
BOX_MM = (20, 30, 50, 10)


def a4() -> svg.Document:
    doc = svg.Document(210 * svg.mm, 297 * svg.mm)
    doc.rect(*BOX_MM, fill="red")
    return doc


def media_boxes(data: bytes) -> list[tuple[float, float]]:
    boxes = re.findall(rb"/MediaBox \[([-\d. ]+)\]", data)
    return [(x1 - x0, y1 - y0) for x0, y0, x1, y1 in (map(float, box.split()) for box in boxes)]


def test_an_a4_document_is_an_a4_pdf_page():
    assert media_boxes(a4().export("pdf")) == [pytest.approx(A4_PT, abs=0.01)]


def test_a_letter_document_is_a_letter_pdf_page():
    assert media_boxes(svg.Document(8.5 * svg.inch, 11 * svg.inch).export("pdf")) == [pytest.approx(LETTER_PT)]


def test_every_pdf_page_keeps_its_own_size_and_a_valid_xref_table():
    data = svg.export.export([a4(), svg.Document(8.5 * svg.inch, 11 * svg.inch), a4()], "pdf")
    assert media_boxes(data) == [pytest.approx(A4_PT, abs=0.01), pytest.approx(LETTER_PT), pytest.approx(A4_PT, abs=0.01)]
    assert int(re.search(rb"startxref\s+(\d+)", data).group(1)) == data.rfind(b"\nxref") + 1
    for offset in re.findall(rb"(?m)^(\d{10}) \d{5} n", data):
        assert re.match(rb"\d+ 0 obj", data[int(offset):])


def test_an_a4_eps_has_an_a4_bounding_box():
    text = a4().export("eps").decode()
    width, height = map(float, re.search(r"%%HiResBoundingBox: 0 0 ([\d.]+) ([\d.]+)", text).groups())
    assert (width, height) == pytest.approx(A4_PT, abs=0.01)
    assert "%%BoundingBox: 0 0 596 842" in text


def test_an_a4_pptx_slide_is_a4_in_emu():
    pptx = pytest.importorskip("pptx")
    deck = pptx.Presentation(io.BytesIO(a4().export("pptx")))
    assert (deck.slide_width, deck.slide_height) == A4_EMU


@pytest.mark.parametrize("name", ["pdf", "eps", "tikz", "pptx"])
def test_a_round_trip_keeps_the_page_size_and_the_shape_position(name):
    if name == "pptx":
        pytest.importorskip("pptx")
    original = a4()
    data = original.export(name)
    back = find_importer(name).function(data if isinstance(data, bytes) else data.encode())
    width, height = (210 * PX_PER_MM, 297 * PX_PER_MM)
    assert (back.root.get("width"), back.root.get("height")) == pytest.approx((width, height), abs=0.01)
    assert tuple(back[0].bounds()) == pytest.approx(tuple(v * PX_PER_MM for v in BOX_MM), abs=0.01)


def test_a_foreign_pdf_point_reads_as_four_thirds_of_a_user_unit():
    data = (b"%PDF-1.1\n1 0 obj << /Type /Page /MediaBox [0 0 72 36] /Contents 2 0 R >> endobj\n"
            b"2 0 obj << /Length 999 >> stream\n0 0 18 9 re f\nendstream endobj\n")
    doc = find_importer("pdf").function(data)
    assert (doc.root.get("width"), doc.root.get("height")) == pytest.approx((96, 48))
    assert tuple(doc[0].bounds()) == pytest.approx((0, 36, 24, 12))


def test_a_foreign_eps_point_reads_as_four_thirds_of_a_user_unit():
    doc = find_importer("eps").function(b"%!PS\n%%BoundingBox: 0 0 72 36\n0 0 18 9 rectfill")
    assert (doc.root.get("width"), doc.root.get("height")) == pytest.approx((96, 48))
    assert tuple(doc[0].bounds()) == pytest.approx((0, 36, 24, 12))


def test_a_foreign_tikz_centimetre_reads_as_its_user_units():
    doc = find_importer("tikz").function(rb"\begin{tikzpicture}\fill (0,0) rectangle (2.54,1);\end{tikzpicture}")
    assert doc[0].bounds().width == pytest.approx(96)


def pixels() -> svg.Document:
    doc = svg.Document(144, 72)
    doc.rect(0, 0, 72, 36, fill="red", stroke="black", stroke_width=2)
    return doc


def test_px_per_inch_72_makes_a_pixel_page_one_point_per_unit():
    assert media_boxes(pixels().export("pdf", px_per_inch=72)) == [pytest.approx((144, 72))]
    assert media_boxes(pixels().export("pdf")) == [pytest.approx((108, 54))]
    text = pixels().export("eps", px_per_inch=72).decode()
    assert "%%HiResBoundingBox: 0 0 144 72" in text and "\n1 1 scale\n" in text
    picture = pixels().export("tikz", px_per_inch=72)
    assert "[x=1bp, y=-1bp]" in picture and "line width=2bp" in picture


@pytest.mark.parametrize("name", ["pdf", "eps", "tikz"])
def test_px_per_inch_keeps_physical_sizes(name):
    assert a4().export(name, px_per_inch=72) == a4().export(name)


@pytest.mark.parametrize("name", ["pdf", "eps", "tikz"])
def test_px_per_inch_must_be_positive(name):
    with pytest.raises(ValueError, match="px_per_inch must be above 0"):
        pixels().export(name, px_per_inch=0)
