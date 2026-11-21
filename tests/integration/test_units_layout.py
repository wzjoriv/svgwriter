"""Physical units through layout, attributes and export: an A4 page laid out in millimetres."""

import io
import re

import pytest

import svgwriter as svg

PT_PER_MM = 72 / 25.4
MEDIA_BOX = re.compile(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]")


def a4_stack() -> tuple[svg.Document, list[svg.Rect]]:
    doc = svg.Document(size=svg.size.a4)
    boxes = [svg.rect(0, 0, 40, 20) for _ in range(3)]
    doc += svg.VStack(*boxes, gap=svg.mm(5), padding=svg.mm(10))
    return doc, boxes


def test_layout_lengths_count_in_page_millimetres():
    doc, boxes = a4_stack()
    assert doc.root.get("viewBox").width == 210
    assert [box.bounds().y for box in boxes] == pytest.approx([10, 35, 60])


def test_attribute_quantities_follow_svg_units_inside_the_page():
    doc = svg.Document(size="a4")
    bar = doc.rect(svg.mm(5), 0, svg.cm(1), 2, stroke_width=svg.pt(1))
    assert 'width="1cm"' in doc.to_string()
    assert bar.bounds().width == pytest.approx(svg.cm(1).to_user_units())


def test_pdf_page_is_exactly_a4_whatever_px_per_inch():
    doc, _ = a4_stack()
    for options in ({}, {"px_per_inch": 300}):
        x0, y0, x1, y1 = (float(v) for v in MEDIA_BOX.search(doc.export("pdf", **options)).groups())
        assert (x1 - x0, y1 - y0) == pytest.approx((210 * PT_PER_MM, 297 * PT_PER_MM), abs=1e-3)


def test_px_per_inch_scales_pixel_sized_pages_only():
    page = svg.Document(96, 48)
    page += svg.HStack(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10), gap=svg.inch(0.25))
    sizes = [tuple(float(v) for v in MEDIA_BOX.search(page.export("pdf", px_per_inch=ppi)).groups()[2:])
             for ppi in (96, 192)]
    assert sizes == [pytest.approx((72, 36)), pytest.approx((36, 18))]


def test_png_dpi_follows_the_physical_page():
    image = pytest.importorskip("PIL.Image")
    doc = svg.Document(svg.inch(2), svg.inch(1))
    doc += svg.HStack(svg.rect(0, 0, svg.inch(0.5), svg.inch(0.5)), svg.circle(0, 0, svg.pt(9)), gap=svg.cm(1))
    assert image.open(io.BytesIO(doc.export("png", dpi=300))).size == (600, 300)


def test_grid_tracks_take_page_units():
    doc = svg.Document(size=svg.size.a4)
    grid = svg.Grid(*[svg.rect(0, 0, 20, 20) for _ in range(4)], columns=2, gap=svg.mm(3), width=svg.mm(100))
    doc += grid
    assert (grid.bounds().width, grid.bounds().height) == (100, 43)
