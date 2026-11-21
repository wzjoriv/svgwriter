import io
import json
import zipfile

import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal._flat._flatten import flatten

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _slide_xml(data):
    from lxml import etree

    return etree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("ppt/slides/slide1.xml"))


def _read_pptx(data):
    return svg.FORMATS.reader("pptx").read(data)


def _linked():
    doc = svg.Document(200, 100)
    link = doc.add(svg.A(href="https://example.com"))
    link.add(svg.rect(10, 10, 40, 40, fill="red"))
    return doc


def test_pptx_keeps_dashes_caps_and_joins():
    pytest.importorskip("pptx")
    doc = svg.Document(200, 100)
    doc.path("M10 10 L100 10 L100 60", fill="none", stroke="blue", stroke_width=4, stroke_dasharray="8 4",
             stroke_linecap="round", stroke_linejoin="bevel")
    data = svg.export.export(doc, "pptx")
    line = _slide_xml(data).find(f".//{A}ln")
    assert line.get("cap") == "rnd" and line.find(f"{A}bevel") is not None
    assert [(d.get("d"), d.get("sp")) for d in line.iter(f"{A}ds")] == [("200000", "100000")]
    back = _read_pptx(data)[0]
    assert back.get("stroke-dasharray") == "8 4"
    assert (back.get("stroke-linecap"), back.get("stroke-linejoin")) == ("round", "bevel")


def test_pptx_miter_join_keeps_its_limit():
    pytest.importorskip("pptx")
    doc = svg.Document(100, 100)
    doc.path("M10 10 L50 50 L90 10", fill="none", stroke="black", stroke_width=2)
    miter = _slide_xml(svg.export.export(doc, "pptx")).find(f".//{A}ln/{A}miter")
    assert miter.get("lim") == "400000"


def test_pptx_linear_gradient_becomes_a_gradient_fill():
    pytest.importorskip("pptx")
    doc = svg.Document(200, 100)
    doc.rect(10, 10, 80, 40, fill=svg.LinearGradient.horizontal("red", "blue"))
    data = svg.export.export(doc, "pptx")
    fill = _slide_xml(data).find(f".//{A}gradFill")
    assert fill.find(f"{A}lin").get("ang") == "0"
    assert [s.find(f"{A}srgbClr").get("val") for s in fill.iter(f"{A}gs")] == ["FF0000", "0000FF"]
    gradient = _read_pptx(data)[0].get("fill").element
    assert gradient.tag == "linearGradient"
    assert (gradient.get("x1"), gradient.get("x2")) == (pytest.approx(10), pytest.approx(90))


def test_pptx_vertical_and_partial_gradients_are_remapped_onto_the_box():
    pytest.importorskip("pptx")
    doc = svg.Document(200, 100)
    doc.rect(0, 0, 100, 100, fill=svg.LinearGradient(svg.Stop(0, "red"), svg.Stop(1, "blue"), x1=0, y1=0, x2=0,
                                                     y2=50, gradient_units="userSpaceOnUse"))
    fill = _slide_xml(svg.export.export(doc, "pptx")).find(f".//{A}gradFill")
    assert fill.find(f"{A}lin").get("ang") == str(90 * 60000)
    stops = [(int(s.get("pos")), s.find(f"{A}srgbClr").get("val")) for s in fill.iter(f"{A}gs")]
    assert stops == [(0, "FF0000"), (50000, "0000FF"), (100000, "0000FF")]


def test_pptx_radial_gradient_is_a_path_gradient_centred_on_the_gradient():
    pytest.importorskip("pptx")
    doc = svg.Document(200, 100)
    doc.rect(0, 0, 100, 100, fill=svg.RadialGradient(svg.Stop(0, "white"), svg.Stop(1, "black")))
    data = svg.export.export(doc, "pptx")
    shade = _slide_xml(data).find(f".//{A}gradFill/{A}path")
    assert shade.get("path") == "circle"
    assert shade.find(f"{A}fillToRect").get("l") == "50000"
    assert _read_pptx(data)[0].get("fill").element.tag == "radialGradient"


def test_pptx_places_images_inside_transformed_groups():
    pptx = pytest.importorskip("pptx")
    doc = svg.Document(200, 100)
    group = doc.add(svg.Group()).translate(50, 20)
    group.add(svg.Image(np.ones((4, 4, 3)), 10, 10, 40, 40))
    picture = next(iter(pptx.Presentation(io.BytesIO(svg.export.export(doc, "pptx"))).slides[0].shapes))
    assert (picture.left, picture.top) == (60 * 9525, 30 * 9525)


def test_pptx_keeps_links_on_shapes():
    pptx = pytest.importorskip("pptx")
    data = svg.export.export(_linked(), "pptx")
    shape = next(iter(pptx.Presentation(io.BytesIO(data)).slides[0].shapes))
    assert shape.click_action.hyperlink.address == "https://example.com"
    back = _read_pptx(data)[0]
    assert back.tag == "a" and back.get("xlink:href") == "https://example.com"


def test_excalidraw_keeps_links():
    text = svg.export.export(_linked(), "excalidraw")
    assert json.loads(text)["elements"][0]["link"] == "https://example.com"
    back = svg.FORMATS.reader("excalidraw").read(text.encode())
    assert back[0].tag == "a"


def test_pdf_links_become_uri_annotations():
    doc = svg.Document(200, 100)
    link = doc.add(svg.Group()).translate(10, 5).add(svg.A(href="https://example.com"))
    link.add(svg.rect(10, 10, 40, 40, fill="red"))
    data = svg.export.export(doc, "pdf")
    assert b"/URI (https://example.com)" in data and b"/Rect [15 33.75 45 63.75]" in data


def test_flatten_records_links():
    assert flatten(_linked()).items[0].link == "https://example.com"


@pytest.mark.parametrize("effect", ["mask", "filter"])
def test_flattening_formats_warn_about_dropped_effects(effect):
    doc = svg.Document(100, 100)
    if effect == "mask":
        mask = doc.define(svg.Mask())
        mask.add(svg.rect(0, 0, 50, 100, fill="white"))
        doc.rect(10, 10, 80, 80, fill="red", mask=mask)
    else:
        blur = doc.define(svg.Filter())
        blur.add(svg.FeGaussianBlur(std_deviation=3))
        doc.rect(10, 10, 80, 80, fill="red", filter=blur)
    with pytest.warns(UserWarning, match=effect):
        svg.export.export(doc, "eps")


def _arrow_doc():
    doc = svg.Document(200, 100)
    tip = doc.define(svg.Marker(svg.path("M0 0 L10 5 L0 10 Z", fill="red"), view_box=(0, 0, 10, 10), ref_x=10,
                                ref_y=5, marker_width=5, marker_height=5, orient="auto"))
    doc.path("M10 50 L150 50 L150 90", fill="none", stroke="black", stroke_width=2, marker_end=tip)
    return doc


def test_markers_are_drawn_in_rasters():
    pixels = _arrow_doc().rasterize()
    assert pixels[80:90, 145:156, 0].max() > 0.9 and pixels[80:90, 145:156, 1].max() < 0.1


@pytest.mark.parametrize("fmt", ["eps", "tikz", "pptx"])
def test_markers_are_drawn_in_vector_formats(fmt):
    if fmt == "pptx":
        pytest.importorskip("pptx")
    data = svg.export.export(_arrow_doc(), fmt)
    back = svg.FORMATS.reader(fmt).read(data if isinstance(data, bytes) else data.encode())
    tip = [e for e in back if str(e.get("fill")) == "#ff0000"]
    assert len(tip) == 1
    box = tip[0].bounds()
    assert box.x == pytest.approx(145, abs=0.5) and box.y + box.height == pytest.approx(90, abs=0.5)


def test_markers_from_parsed_svg_and_every_vertex():
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"><defs>'
        '<marker id="dot" markerWidth="4" markerHeight="4" refX="2" refY="2" markerUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="2" fill="blue"/></marker></defs>'
        '<polyline points="10,20 50,20 90,20" fill="none" stroke="black" marker-start="url(#dot)" '
        'marker-mid="url(#dot)" marker-end="url(#dot)"/></svg>')
    back = svg.FORMATS.reader("eps").read(svg.export.export(doc, "eps"))
    centres = sorted(round(e.bounds().x + 2) for e in back if str(e.get("fill")) == "#0000ff")
    assert centres == [10, 50, 90]


def test_relative_paths_choose_the_format_by_extension():
    assert svg.FORMATS.writer("../figure.pdf").name == "pdf"
    assert svg.FORMATS.writer("./a.b/figure.svgz").name == "svgz"
    assert svg.FORMATS.writer(".png").name == "png"


def test_excalidraw_keeps_text_and_images():
    doc = svg.Document(200, 100)
    doc.text("Hello", x=10, y=50, font_size=20, fill="#ff0000")
    doc.add(svg.Group()).translate(50, 20).add(svg.Image(np.ones((4, 4, 3)), 10, 10, 40, 40))
    scene = json.loads(svg.export.export(doc, "excalidraw"))
    assert sorted(e["type"] for e in scene["elements"]) == ["image", "text"]
    assert len(scene["files"]) == 1
    back = svg.FORMATS.reader("excalidraw").read(json.dumps(scene).encode())
    text = next(e for e in back if e.tag == "text")
    image = next(e for e in back if e.tag == "image")
    assert text.text_content == "Hello" and (text.get("x"), text.get("y")) == (pytest.approx(10), pytest.approx(50))
    assert (image.get("x"), image.get("y")) == (60, 30)


def test_tikz_text_nodes_read_back_as_text():
    doc = svg.Document(200, 100)
    doc.text("Hello", x=10, y=50, font_size=20, fill="#ff0000", font_weight="bold", font_style="italic")
    back = svg.FORMATS.reader("tikz").read(svg.export.export(doc, "tikz").encode())
    text = back[0]
    assert text.tag == "text" and text.text_content == "Hello"
    assert (text.get("x"), text.get("y"), text.get("font-size")) == pytest.approx((10, 50, 20), abs=1e-3)
    assert (text.get("fill"), text.get("font-weight"), text.get("font-style")) == ("#ff0000", "bold", "italic")
    assert text.get("font-family") == "sans-serif" and text.get("text-anchor") == "start"


def test_tikz_rotated_text_keeps_its_turn():
    doc = svg.Document(200, 100)
    doc.text("Turn", x=100, y=50, font_size=12).rotate(30, about=(100, 50))
    back = svg.FORMATS.reader("tikz").read(svg.export.export(doc, "tikz").encode())
    assert back[0].bounds().y < 50 < back[0].bounds().y + back[0].bounds().height + 10
    assert back[0].t.b == pytest.approx(0.5, abs=1e-6)


def test_markers_from_a_parsed_file_render(tmp_path) -> None:
    import svgwriter as svg

    doc = svg.Document(60, 30)
    marker = doc.defs.add(svg.markers.arrow(id="tip"))
    doc.add(svg.path("M5 15 L50 15", stroke="black", stroke_width=2, marker_end=marker))
    path = tmp_path / "markers.svg"
    doc.save(path)
    pixels = svg.Document.open(path).rasterize()
    assert pixels[..., 3].sum() > 0
