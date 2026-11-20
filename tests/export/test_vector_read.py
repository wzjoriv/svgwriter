from __future__ import annotations

import zlib

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.export import find_importer

TOLERANCE = 0.01


def drawing() -> svg.Document:
    doc = svg.Document(200, 100)
    doc.rect(10, 10, 50, 30, fill="red")
    curve = doc.add(svg.Path(fill="none", stroke="blue", stroke_width=2))
    curve.move_to(70, 80).curve_to(90, 10, 120, 10, 140, 80)
    doc.circle(170, 50, 20, fill="#00aa00")
    doc.rect(20, 50, 40, 40, fill="black", opacity=0.5)
    return doc


def paints(doc: svg.Document) -> list[tuple[str, str]]:
    return [(str(e.get("fill")), str(e.get("stroke"))) for e in doc]


def assert_same_geometry(original: svg.Document, back: svg.Document) -> None:
    assert len(back) == len(original)
    for a, b in zip(original, back, strict=True):
        (ax, ay, aw, ah), (bx, by, bw, bh) = a.bounds(), b.bounds()
        assert (bx, by, bw, bh) == pytest.approx((ax, ay, aw, ah), abs=TOLERANCE)


@pytest.mark.parametrize("name", ["pdf", "eps", "tikz"])
def test_round_trip(name: str) -> None:
    doc = drawing()
    data = doc.export(name)
    back = find_importer(name).function(data.encode() if isinstance(data, str) else data)
    assert_same_geometry(doc, back)
    assert paints(back) == [("#ff0000", "None"), ("none", "#0000ff"), ("#00aa00", "None"), ("#000000", "None")]
    assert back[1].get("stroke-width") == pytest.approx(2)
    assert (back.root.get("width"), back.root.get("height")) == pytest.approx((200, 100))


@pytest.mark.parametrize("name", ["pdf", "tikz"])
def test_round_trip_keeps_opacity(name: str) -> None:
    data = drawing().export(name)
    back = find_importer(name).function(data.encode() if isinstance(data, str) else data)
    assert back[3].get("opacity") == pytest.approx(0.5) and back[0].get("opacity") is None


@pytest.mark.parametrize("name", ["eps", "tikz"])
def test_round_trip_dashes_and_fill_with_stroke(name: str) -> None:
    doc = svg.Document(50, 50)
    doc.rect(5, 5, 20, 20, fill="yellow", stroke="purple", stroke_width=3, stroke_dasharray="4 2")
    data = doc.export(name)
    back = find_importer(name).function(data.encode() if isinstance(data, str) else data)
    path, = back
    assert (path.get("fill"), path.get("stroke"), path.get("stroke-dasharray")) == ("#ffff00", "#800080", "4 2")


def test_load_and_save_through_registry(tmp_path) -> None:
    for suffix in (".pdf", ".eps", ".ps", ".tex", ".tikz"):
        target = svg.export.save(drawing(), tmp_path / f"figure{suffix}")
        assert len(svg.export.load(target)) == 4


def pdf_file(pages: list[bytes], extra: list[bytes] = (), fonts: dict[str, str] | None = None) -> bytes:
    """A PDF with one Flate-compressed content stream per page and a deliberately broken xref table."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(len(pages))).encode()
    objects.append(b"<< /Type /Pages /Kids [" + kids + b"] /Count %d /MediaBox [0 0 100 50] >>" % len(pages))
    xobject = 3 + 2 * len(pages)
    font_start = 3 + 2 * len(pages) + len(extra)
    font_names = list((fonts or {}).items())
    font_table = b" ".join(b"/%s %d 0 R" % (name.encode(), font_start + i) for i, (name, _) in enumerate(font_names))
    for i, content in enumerate(pages):
        packed = zlib.compress(content)
        objects.append(b"<< /Type /Page /Parent 2 0 R /Contents %d 0 R /Resources << /ExtGState << /Half << /ca 0.5 >> >>"
                       b" /XObject << /F1 %d 0 R >> /Font << %s >> >> >>" % (4 + 2 * i, xobject, font_table))
        objects.append(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(packed) + packed + b"\nendstream")
    objects += extra
    objects += [b"<< /Type /Font /Subtype /Type1 /BaseFont /%s >>" % base.encode() for _, base in font_names]
    body = b"".join(b"%d 0 obj\n" % (n + 1) + obj + b"\nendobj\n" for n, obj in enumerate(objects))
    return b"%PDF-1.4\n" + body + b"xref\n0 1\ngarbage\ntrailer << /Root 1 0 R >>\nstartxref\n12345\n%%EOF\n"


FORM = (b"<< /Type /XObject /Subtype /Form /BBox [0 0 100 50] /Matrix [1 0 0 1 50 0] /Length 22 >>\n"
        b"stream\n0 0 1 rg 0 0 10 10 re f\nendstream")

PAGE_ONE = b"""
q 1 0 0 RG 4 w [2 1] 0 d 10 40 m 30 40 l S Q
/DeviceRGB cs 0 1 0 sc /Half gs 10 10 20 10 re f
1 0 0 0 k 1 0 0 1 0 0 cm 40 10 m 50 20 60 10 v 60 0 y h f*
BT /F1 12 Tf (ignored text with re f) Tj ET
0 0 50 50 re W n
/F1 Do
"""


class TestPdf:
    def test_flate_form_state_and_colors(self) -> None:
        doc = find_importer("pdf").function(pdf_file([PAGE_ONE, b"0 g 0 0 5 5 re f"], [FORM]))
        assert (doc.root.get("width"), doc.root.get("height")) == (100, 50)
        line, square, curve, text, form = doc
        assert text.tag == "text" and text.text_content == "ignored text with re f" and text.get("font-size") == 12
        assert form.get("clip-path") is not None
        assert line.get("stroke") == "#ff0000" and line.get("stroke-width") == 4 and line.get("stroke-dasharray") == "2 1"
        assert line.bounds().y == pytest.approx(10)
        assert square.get("fill") == "#00ff00" and square.get("opacity") == 0.5
        assert square.bounds() == pytest.approx((10, 30, 20, 10))
        assert curve.get("fill") == "#00ffff" and curve.get("fill-rule") == "evenodd"
        assert form.get("fill") == "#0000ff" and form.bounds() == pytest.approx((50, 40, 10, 10))

    def test_page_option(self, tmp_path) -> None:
        path = tmp_path / "two.pdf"
        path.write_bytes(pdf_file([PAGE_ONE, b"0 g 0 0 5 5 re f"], [FORM]))
        second = svg.export.load(path, page=1)
        assert len(second) == 1 and second[0].bounds() == pytest.approx((0, 45, 5, 5))
        with pytest.raises(ValueError, match="page 2 out of range"):
            svg.export.load(path, page=2)

    def test_uncompressed_stream_without_catalog(self) -> None:
        data = (b"%PDF-1.1\n1 0 obj << /Type /Page /MediaBox [0 0 20 20] /Contents 2 0 R >> endobj\n"
                b"2 0 obj << /Length 999 >> stream\n0.5 G 2 2 m 18 18 l S\nendstream endobj\n")
        line, = find_importer("pdf").function(data)
        assert line.get("stroke") == "#808080" and line.bounds() == pytest.approx((2, 2, 16, 16))

    def test_bad_input(self) -> None:
        reader = find_importer("pdf").function
        with pytest.raises(ValueError, match="not a PDF"):
            reader(b"hello world")
        with pytest.raises(ValueError, match="no pages"):
            reader(b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n")


EPS_PROCEDURES = b"""%!PS-Adobe-3.0 EPSF-3.0
%%BoundingBox: 0 0 100 100
%%EndComments
/m {moveto} bind def
/l /lineto load def
/box { /s exch def /y exch def /x exch def x y m s 0 rlineto 0 s rlineto s neg 0 rlineto closepath } def
gsave 10 10 translate 0.5 setgray 0 0 20 box fill grestore
0 0 1 setrgbcolor 50 50 10 0 360 arc stroke
pop pop exch dup moveto lineto curveto unknownop 1 2 3
0 1 0 0 setcmykcolor [3 1] 0 setdash 2 setlinewidth 1 setlinecap 0 90 m 90 90 l stroke
gsave 90 10 translate 90 rotate 2 2 scale 0 0 5 5 rectfill grestore
showpage
0 0 m 100 100 l stroke
"""


class TestEps:
    def test_procedures_and_operators(self) -> None:
        doc = find_importer("eps").function(EPS_PROCEDURES)
        box, circle, dashed, rotated = doc
        assert box.get("fill") == "#808080" and box.bounds() == pytest.approx((10, 70, 20, 20))
        assert circle.get("stroke") == "#0000ff" and circle.bounds() == pytest.approx((40, 40, 20, 20), abs=TOLERANCE)
        assert dashed.get("stroke") == "#ff00ff" and dashed.get("stroke-dasharray") == "3 1"
        assert dashed.get("stroke-linecap") == "round" and dashed.get("stroke-width") == 2
        assert rotated.bounds() == pytest.approx((80, 80, 10, 10))

    def test_arcn_and_relative_curve(self) -> None:
        doc = find_importer("eps").function(b"%!PS\n0 0 moveto 10 0 rlineto 10 0 10 180 0 arcn 0 10 0 10 10 10 rcurveto stroke")
        path, = doc
        assert (path.bounds().width, path.bounds().height) == pytest.approx((30, 10), abs=TOLERANCE)

    def test_dictionary_scope_and_saved_path(self) -> None:
        program = b"""%!PS
        /l {lineto} def
        /Glyphs 2 dict dup begin /l {0 0 moveto 99 99 lineto stroke} def end def
        << /k 5 >> begin 0 0 moveto k k l end
        1 0 0 setrgbcolor gsave fill grestore 0 setgray stroke"""
        path, = find_importer("eps").function(program)
        assert (path.get("fill"), path.get("stroke")) == ("#ff0000", "#000000")
        assert path.bounds().width == pytest.approx(5)

    def test_bad_input(self) -> None:
        with pytest.raises(ValueError, match="not PostScript"):
            find_importer("eps").function(b"\x00\x01garbage")

    @pytest.mark.parametrize("angle", [0, 30, 90])
    def test_exported_image_round_trip(self, angle: int) -> None:
        pixels = np.zeros((4, 6, 3))
        pixels[0, 0], pixels[3, 5] = (1, 0, 0), (0, 0, 1)
        doc = svg.Document(100, 80)
        original = doc.add(svg.Image(pixels, 20, 10, 36, 24, preserve_aspect_ratio="none"))
        original.t = svg.Matrix.rotate(angle, 38, 22)
        back = find_importer("eps").function(svg.export.export(doc, "eps"))
        image = next(e for e in back.root.iter() if e.tag == "image")
        assert image.bounds() == pytest.approx(original.bounds(), abs=0.5)
        assert image.rgba()[0, 0].tolist() == pytest.approx([1, 0, 0, 1], abs=0.02)
        assert image.rgba()[3, 5].tolist() == pytest.approx([0, 0, 1, 1], abs=0.02)

    def test_image_from_procedure(self) -> None:
        program = b"%!PS\n%%BoundingBox: 0 0 20 10\n20 10 scale 2 1 8 [2 0 0 1 0 0] {<ff00>} image"
        image = next(e for e in find_importer("eps").function(program).root.iter() if e.tag == "image")
        assert image.rgba()[0, :, 0].tolist() == pytest.approx([1, 0])

    def test_text_font_and_position(self) -> None:
        program = b"%!PS\n%%BoundingBox: 0 0 100 50\n/Helvetica-Bold findfont 12 scalefont setfont 10 10 moveto (Hi) show"
        text = next(e for e in find_importer("eps").function(program).root.iter() if e.tag == "text")
        assert text.text_content == "Hi" and text.get("font-size") == 12
        assert text.get("font-family") == "Helvetica" and text.get("font-weight") == "bold"
        assert text.t.apply(0, 0) == pytest.approx((10, 40))

    def test_text_advances_current_point(self) -> None:
        program = b"%!PS\n%%BoundingBox: 0 0 100 50\n/Times-Roman 10 selectfont 5 5 moveto (AB) show (C) show"
        first, second = (e for e in find_importer("eps").function(program).root.iter() if e.tag == "text")
        assert second.t.apply(0, 0)[0] > first.t.apply(0, 0)[0] + 5

    def test_clip_intersects_and_restores(self) -> None:
        program = b"""%!PS
%%BoundingBox: 0 0 100 100
gsave 10 10 moveto 60 10 lineto 60 60 lineto 10 60 lineto closepath clip
newpath 30 30 moveto 90 30 lineto 90 90 lineto 30 90 lineto closepath clip
newpath 0 0 100 100 rectfill grestore 1 0 0 setrgbcolor 0 0 5 5 rectfill"""
        clipped, plain = find_importer("eps").function(program)
        assert clipped.get("clip-path") is not None and plain.get("clip-path") is None
        assert "M30 40 L60 40 L60 70 L30 70 Z" in find_importer("eps").function(program).export("svg")


TIKZ = r"""
\documentclass{standalone}
\usepackage{tikz}
\definecolor{mine}{HTML}{336699}
\definecolor{soft}{RGB}{255,128,0}
\begin{document}
\begin{tikzpicture}
  % \draw (9,9) -- (10,10);
  \draw[thick, red] (0,0) -- (1,0) |- (2,1) -- cycle;
  \filldraw[fill=soft, draw=mine, line width=1pt, opacity=.5] (3,0) circle (0.5);
  \fill[green!50!black] (0,2) rectangle ++(1,1) node[above] {label};
  \draw[dashed] (0pt,0pt) .. controls (10pt,10pt) and (20pt,10pt) .. (30pt,0pt);
  \path[draw=blue, fill=mine] (5,5) circle[radius=3pt];
\end{tikzpicture}
\end{document}
"""


class TestTikz:
    def test_hand_written(self) -> None:
        cm = 72.27 / 2.54
        triangle, circle, square, curve, dot = find_importer("tikz").function(TIKZ.encode())
        assert triangle.get("stroke") == "#ff0000" and triangle.get("stroke-width") == 0.8 and triangle.get("fill") == "none"
        assert triangle.bounds() == pytest.approx((0, -cm, 2 * cm, cm))
        assert (circle.get("fill"), circle.get("stroke"), circle.get("opacity")) == ("#ff8000", "#336699", 0.5)
        assert circle.bounds() == pytest.approx((2.5 * cm, -0.5 * cm, cm, cm), abs=TOLERANCE)
        assert square.get("fill") == "#008000" and square.bounds() == pytest.approx((0, -3 * cm, cm, cm))
        assert curve.get("stroke-dasharray") == "3 3" and curve.bounds().width == pytest.approx(30)
        assert dot.bounds().width == pytest.approx(6, abs=TOLERANCE) and dot.get("fill") == "#336699"

    def test_bounding_box_sets_the_page(self) -> None:
        doc = find_importer("tikz").function(rb"\begin{tikzpicture}[x=1pt,y=-1pt]\useasboundingbox (0,0) rectangle (40,20);"
                                             rb"\fill (5,5) rectangle (10,10);\end{tikzpicture}")
        assert doc.root.view_box == (0, 0, 40, 20) and doc[0].bounds() == pytest.approx((5, 5, 5, 5))

    def test_bad_input(self) -> None:
        with pytest.raises(ValueError, match="not TikZ"):
            find_importer("tikz").function(b"just some text")


class TestPdfContent:
    def test_images_and_clips_round_trip(self) -> None:
        doc = svg.Document(100, 60)
        doc.add(svg.Image(np.ones((4, 6, 3)) * [1, 0, 0], 10, 10, 30, 20))
        doc.circle(70, 30, 20, fill="teal").clip(svg.rect(60, 20, 30, 30))
        back = find_importer("pdf").function(svg.export.export(doc, "pdf"))
        tags = [e.tag for e in back.root.iter()]
        assert "image" in tags and "clipPath" in tags
        image = next(e for e in back.root.iter() if e.tag == "image")
        assert image.bounds() == pytest.approx((10, 10, 30, 20), abs=0.5)
        assert image.rgba()[0, 0].tolist() == pytest.approx([1, 0, 0, 1], abs=0.02)

    def test_text_position_and_font(self) -> None:
        page = b"BT /F2 20 Tf 1 0 0 1 10 30 Tm (Hi) Tj ET"
        data = pdf_file([page], [], fonts={"F2": "ABCDEF+Helvetica-Bold"})
        text = next(e for e in find_importer("pdf").function(data).root.iter() if e.tag == "text")
        assert text.text_content == "Hi" and text.get("font-size") == 20 and text.get("font-weight") == "bold"
        assert text.get("font-family") == "Helvetica"


def test_tikz_nodes_become_text():
    from svgwriter.export._vector._tikz_read import read_tikz

    doc = read_tikz(r"\begin{tikzpicture}\draw (0,0) rectangle (2,1);"
                    r"\node[blue] (a) at (1,0.5) {\textbf{Hello} \\ world};\end{tikzpicture}")
    text = next(e for e in doc if e.tag == "text")
    box = next(e for e in doc if e.tag == "path").bounds()
    assert text.text_content == "Hello world" and text.get("fill") == "#0000ff"
    assert text.get("x") == pytest.approx(box.x + box.width / 2)
