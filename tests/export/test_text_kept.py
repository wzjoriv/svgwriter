"""Text stays text in vector exports where the format allows it."""

from __future__ import annotations

import svgwriter as svg
from svgwriter.formats.export._vector._eps import to_eps
from svgwriter.formats.export._vector._tikz import to_tikz
from svgwriter.ops.text import text_outline

MIXED = "a 你好 नमस्ते"


def _doc(text: str) -> svg.Document:
    doc = svg.Document(200, 40)
    doc.text(text, x=10, y=28, font_size=16, fill="red")
    return doc


def test_eps_writes_ascii_with_show() -> None:
    eps = to_eps(_doc("Hello (world)"))
    assert "/Helvetica findfont" in eps
    assert "(Hello \\(world\\)) show" in eps


def test_eps_outlines_non_ascii() -> None:
    eps = to_eps(_doc(MIXED))
    assert ") show" not in eps
    assert "fill" in eps


def test_eps_text_false_draws_outlines() -> None:
    assert "findfont" not in to_eps(_doc("Hello"), text=False)


def test_tikz_writes_nodes() -> None:
    tikz = to_tikz(_doc("50% & more"))
    assert "\\node[" in tikz
    assert "50\\% \\& more" in tikz
    assert "\\node" not in to_tikz(_doc("x"), text=False)


def test_mixed_scripts_shape_each_in_its_own_font() -> None:
    whole = len(text_outline(MIXED, "sans-serif", 16))
    parts = sum(len(text_outline(part, "sans-serif", 16)) for part in MIXED.split(" "))
    assert whole >= parts * 0.9


def test_pptx_keeps_text_as_editable_boxes() -> None:
    from svgwriter.formats.export import export, find_importer

    doc = svg.Document(300, 120)
    doc.text("Hello slide", x=20, y=40, font_size=24, fill="red", font_weight="bold")
    turned = doc.text("turned", x=150, y=90, font_size=18, font_style="italic")
    turned.rotate(-20, about=(150, 90))
    back = find_importer("pptx").function(export(doc, "pptx"))
    texts = [element for element in back.root.iter() if element.tag == "text"]
    assert [text.text_content for text in texts] == ["Hello slide", "turned"]
    assert float(texts[0].get("y")) == 40
    assert texts[0].get("font-weight") == "bold"
    assert texts[1].get("font-style") == "italic"
    assert "path" not in back.to_string()


def _pdf_text_objects(data: bytes) -> int:
    import re
    import zlib

    count = 0
    for stream in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            stream = zlib.decompress(stream)
        except zlib.error:
            pass
        count += len(re.findall(rb"(?m)^BT$", stream))
    return count


def test_pdf_keeps_plain_text_as_text() -> None:
    from svgwriter.formats.export import export

    doc = _doc("Hello")
    assert _pdf_text_objects(export(doc, "pdf")) > 0
    assert _pdf_text_objects(export(doc, "pdf", text=False)) == 0


def test_pdf_outlines_text_it_cannot_keep() -> None:
    from svgwriter.formats.export import export

    doc = svg.Document(100, 40)
    doc.text("Hello", x=10, y=28, font_size=16, fill=svg.LinearGradient(svg.Stop(0, "red"), svg.Stop(1, "blue")))
    assert _pdf_text_objects(export(doc, "pdf")) == 0


def test_pdf_text_matches_outline_render() -> None:
    import numpy as np

    from svgwriter.formats.export import export, find_importer

    doc = svg.Document(120, 40)
    doc.rect(0, 0, 120, 40, fill="white")
    doc.text("Hello", x=10, y=28, font_size=20, fill="red")
    read = find_importer("pdf").function
    back = read(export(doc, "pdf"))
    texts = [element for element in back.root.iter() if element.tag == "text"]
    assert [text.text_content for text in texts] == ["Hello"]
    assert np.abs(back.rasterize() - doc.rasterize()).mean() < 0.02
