"""Typefaces from font files inside layouts: measuring with the face's metrics, embedding and outlining."""

import base64
import re

import pytest

import svgwriter as svg

from .conftest import BOLD_GLYPH, GLYPH

EM = 1000
SIZE = 10
ASCENT, DESCENT = 0.8, 0.2
GAP = 2


def advance(glyph: int) -> float:
    return (glyph + 100) * SIZE / EM


def test_vstack_measures_with_the_face_metrics(typeface):
    regular = svg.text("AA", font_family=typeface, font_size=SIZE)
    bold = svg.text("AA", font=typeface, font_size=SIZE, font_weight="bold")
    stack = svg.VStack(regular, bold, gap=GAP)
    line = (ASCENT + DESCENT) * SIZE
    assert stack.bounds().height == pytest.approx(2 * line + GAP)
    assert stack.bounds().width == pytest.approx(2 * advance(BOLD_GLYPH))
    assert bold.bounds().width == pytest.approx(advance(BOLD_GLYPH) + BOLD_GLYPH * SIZE / EM)
    assert regular.bounds().width == pytest.approx(advance(GLYPH) + GLYPH * SIZE / EM)


def test_embed_fonts_after_layout_writes_each_used_face_once(typeface, font_files):
    doc = svg.Document(100, 60)
    doc += svg.VStack(svg.text("AA", font_family=typeface, font_size=SIZE),
                      svg.text("A", font_family=typeface, font_size=SIZE, font_weight=700),
                      svg.text("A", font_family=typeface, font_size=SIZE), gap=GAP)
    sheet = doc.embed_fonts(typeface)
    text = doc.to_string()
    sources = re.findall(r"base64,([A-Za-z0-9+/=]+)", sheet.css)
    assert text.count("@font-face") == 2
    assert {base64.b64decode(s) for s in sources} == {path.read_bytes() for path in font_files}


def test_theme_font_family_picks_the_face_for_the_role_weight(typeface):
    theme = svg.Theme.get("light").replace(fonts={"family": typeface.name})
    doc = svg.Document(100, 60, theme=theme)
    doc += svg.VStack(svg.text("AA").as_role("title"), svg.text("AA").as_role("text"))
    assert [face.weight for face in doc.used_faces(typeface)] == [(700, 700), (400, 400)]


def test_to_path_of_laid_out_text_keeps_the_placed_outline(typeface):
    text = svg.text("AA", font_family=typeface, font_size=SIZE)
    stack = svg.VStack(svg.rect(0, 0, 30, 12), text, gap=GAP).translate(5, 5)
    outline = text.to_path()
    assert outline.bounds() == text.bounds()
    assert outline.bounds().y == pytest.approx(12 + GAP + (ASCENT - 0.7) * SIZE)
    assert stack.bounds().y == 5
