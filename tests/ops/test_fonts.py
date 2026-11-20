import io

import pytest

import svgwriter as svg
from svgwriter._internal import _fonts, _shaping

EM = 1000


def _box_font(family: str) -> bytes:
    """A one-glyph TrueType font: 'A' is a 600 x 700 box."""
    builder = pytest.importorskip("fontTools.fontBuilder")
    pens = pytest.importorskip("fontTools.pens.ttGlyphPen")
    fb = builder.FontBuilder(EM, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({ord("A"): "A"})
    pen = pens.TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 700))
    pen.lineTo((600, 700))
    pen.lineTo((600, 0))
    pen.closePath()
    fb.setupGlyf({".notdef": pens.TTGlyphPen(None).glyph(), "A": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (700, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    buffer = io.BytesIO()
    fb.save(buffer)
    return buffer.getvalue()


def test_registered_font_drives_layout_and_outlines():
    name = svg.register_font(_box_font("SvgwBoxTest"))
    assert name == "SvgwBoxTest"
    text = svg.text("A", x=0, y=100, font_family=name, font_size=100)
    box = text.to_path().exact_bbox()
    assert (box.width, box.height) == pytest.approx((60, 70), abs=0.5)
    assert svg.ops.text_width("AA", name, 100) == pytest.approx(140, abs=0.5)


def test_family_override_and_bad_data():
    assert svg.register_font(_box_font("Ignored"), family="My Boxes") == "My Boxes"
    with pytest.raises(ValueError, match="font"):
        svg.register_font(b"not a font")


def _covered(char):
    font = _fonts.font_for(char, "sans-serif", 20)
    return font.unicharToGlyph(ord(char)) != 0


def test_complex_scripts_are_shaped_when_harfbuzz_is_installed():
    pytest.importorskip("uharfbuzz")
    conjunct = "क्ष"
    if not _covered(conjunct[0]):
        pytest.skip("no Devanagari font installed")
    boxes = svg.text(conjunct, x=0, y=40, font_size=32).layout()
    assert len(boxes) == 3
    assert sum(1 for box in boxes if len(box.outline)) < 3
    assert boxes[-1].advance > 0 and not _shaping.needs_shaping("plain latin")


@pytest.mark.parametrize("char", ["你", "こ", "আ", "न"])
def test_missing_glyphs_fall_back_to_a_system_font(char):
    if not _covered(char):
        pytest.skip("no font for this script installed")
    outline, advance = svg.ops.text.glyph_shape(char, "serif", 20)
    assert len(outline) and advance > 0


def test_language_hint_is_used_for_fallback():
    text = svg.text("你", x=0, y=20, xml_lang="zh")
    assert text.layout()[0].advance > 0
