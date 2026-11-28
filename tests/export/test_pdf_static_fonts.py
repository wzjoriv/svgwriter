import re

import pytest
import skia

import svgwriter as svg
from svgwriter._internal._typography._font_match import variation_axes

pytest.importorskip("fontTools.varLib.instancer")
CANDIDATES = ("Bahnschrift", "Noto Sans", "Inter", "Roboto Flex", "Source Sans 3")


def _variable_family() -> str:
    for name in CANDIDATES:
        typeface = skia.Typeface(name)
        if typeface.getFamilyName().lower() == name.lower() and variation_axes(typeface):
            return name
    pytest.skip("no variable font installed")


def test_variable_fonts_embed_as_truetype_and_keep_their_weight(tmp_path):
    family = _variable_family()
    doc = svg.Document(300, 50)
    text = doc.text("Formats audit", x=10, y=35, font_size=22, font_family=family)
    text[8:13].wrap(font_weight="bold")
    path = tmp_path / "variable.pdf"
    doc.save(path)
    data = path.read_bytes()
    assert b"/Type3" not in data and b"/FontFile2" in data
    back = svg.Document.open(path)
    assert {e.get("font-weight") for e in back.root.iter() if e.tag == "text"} == {None, "bold"}
    assert len(set(re.findall(rb"/BaseFont\s*/([^\s/>]+)", data))) >= 2
