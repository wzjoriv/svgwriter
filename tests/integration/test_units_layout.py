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


def test_attribute_lengths_count_in_page_millimetres():
    doc = svg.Document(size="a4")
    bar = doc.rect(svg.mm(5), 0, svg.cm(1), "1in", stroke_width=svg.pt(1))
    assert 'x="5" y="0" width="10" height="25.4"' in doc.to_string()
    assert bar.bounds().width == 10 and bar.stroke_width == pytest.approx(25.4 / 72)


def test_lengths_set_before_joining_the_page_convert_on_arrival():
    doc = svg.Document(size="a4")
    bar = svg.rect(0, 0, svg.mm(20), svg.mm(5), style=svg.Style(stroke_width=svg.mm(2)))
    doc += svg.group(bar)
    assert (bar.attributes["width"], bar.style["stroke-width"]) == (20, 2)


def test_svg_text_keeps_svg_units():
    doc = svg.Document.from_string('<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
                                   'viewBox="0 0 210 297"><rect width="20mm" height="1"/></svg>')
    assert 'width="20mm"' in doc.to_string()


def test_path_tools_take_page_millimetres():
    doc = svg.Document(size="a4")
    square = doc.rect(0, 0, 40, 40)
    assert square.round_corners(svg.mm(3)).bounds().width == pytest.approx(40)
    assert square.between(0, svg.mm(10), by="length").total_length() == pytest.approx(10)


def test_a_20mm_rect_is_20mm_in_the_pdf_and_the_browser_render(tmp_path):
    doc = svg.Document(size="a4")
    doc.rect(0, 0, svg.mm(20), svg.mm(20), fill="black")
    pdf = tmp_path / "page.pdf"
    doc.save(pdf)
    back = svg.Document.open(pdf)
    millimetres_per_unit = 210 / float(back.root.get("width"))
    square = min((element for element in back.root.iter() if element.tag in {"rect", "path"}),
                 key=lambda element: element.bounds().width)
    assert square.bounds().width * millimetres_per_unit == pytest.approx(20, abs=0.05)
    doc.rect(0, 30, svg.mm(210), 1, fill="black")
    pixels = svg.ops.render_svg(doc.to_string(), 800, 1200)[..., 3] > 0.5
    square, page = pixels[:20].any(axis=0).sum(), pixels[100:].any(axis=0).sum()
    assert square / page == pytest.approx(20 / 210, abs=0.005)


def test_pdf_page_is_exactly_a4_whatever_units_per_inch():
    doc, _ = a4_stack()
    for options in ({}, {"units_per_inch": 300}):
        x0, y0, x1, y1 = (float(v) for v in MEDIA_BOX.search(doc.export("pdf", **options)).groups())
        assert (x1 - x0, y1 - y0) == pytest.approx((210 * PT_PER_MM, 297 * PT_PER_MM), abs=1e-3)


def test_units_per_inch_scales_pixel_sized_pages_only():
    page = svg.Document(96, 48)
    page += svg.HStack(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10), gap=svg.inch(0.25))
    sizes = [tuple(float(v) for v in MEDIA_BOX.search(page.export("pdf", units_per_inch=ppi)).groups()[2:])
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


def test_png_takes_units_per_inch_like_pdf():
    image = pytest.importorskip("PIL.Image")
    chart = svg.Document(144, 72)
    assert image.open(io.BytesIO(chart.export("png", dpi=100, units_per_inch=72))).size == (200, 100)
    page = svg.Document(svg.inch(2), svg.inch(1))
    assert image.open(io.BytesIO(page.export("png", dpi=100, units_per_inch=72))).size == (200, 100)
