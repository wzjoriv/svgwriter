from __future__ import annotations

import io
from pathlib import Path

import pytest

import svgwriter as svg

ttLib = pytest.importorskip("fontTools.ttLib")


def _letters() -> svg.FontBuilder:
    fb = svg.FontBuilder(family="Test Hand", scale=10, cap_height=720, x_height=480)
    fb.glyph("A", svg.path("M0 0 L30 -72 L60 0 M12 -28 H48", fill="none", stroke="black", stroke_width=8,
                           stroke_linecap="round"), left=40, right=40)
    fb.glyph("V", svg.path("M0 -72 L30 0 L60 -72", fill="none", stroke="black", stroke_width=8), left=40, right=40)
    fb.glyph("o", svg.circle(25, -25, 25) - svg.circle(25, -25, 15), left=50, right=50)
    fb.kern("A", "V", -80)
    return fb


def _font(fb: svg.FontBuilder, file_format: str = "otf") -> ttLib.TTFont:
    return ttLib.TTFont(io.BytesIO(fb.to_bytes(file_format)))


def test_metrics_names_and_cmap() -> None:
    font = _font(_letters())
    assert font["head"].unitsPerEm == 1000
    assert (font["hhea"].ascent, font["hhea"].descent) == (800, -200)
    assert (font["OS/2"].sCapHeight, font["OS/2"].sxHeight, font["OS/2"].usWeightClass) == (720, 480, 400)
    assert font["name"].getDebugName(1) == "Test Hand"
    cmap = font.getBestCmap()
    assert (cmap[ord("A")], cmap[ord(" ")]) == ("A", "uni0020")
    assert font.getGlyphOrder()[0] == ".notdef"


def test_advance_is_outline_width_plus_bearings() -> None:
    fb = _letters()
    assert fb.advance("o") == 600
    assert _font(fb)["hmtx"]["o"] == (600, 50)


def test_explicit_advance_and_empty_glyph_need_advance() -> None:
    fb = svg.FontBuilder()
    fb.glyph("I", svg.rect(0, -700, 100, 700), advance=300)
    assert fb.advance("I") == 300
    with pytest.raises(ValueError, match="advance"):
        fb.glyph("-")
    with pytest.raises(ValueError, match="one character"):
        fb.glyph("ab", svg.rect(0, 0, 1, 1))


@pytest.mark.parametrize("file_format", ["otf", "ttf"])
def test_rendered_outline_matches_source_bounds(file_format: str) -> None:
    fb = svg.FontBuilder(family=f"Bounds {file_format}")
    source = svg.group(svg.rect(0, -600, 200, 600), svg.circle(300, -100, 100))
    fb.glyph("B", source, left=50)
    typeface = svg.Typeface.from_files(fb.to_bytes(file_format))
    box = svg.text("B", x=0, y=0, font_family=typeface, font_size=1000).to_path().bbox
    expected = svg.ops.bounds(source)
    assert box.width == pytest.approx(expected.width, abs=2)
    assert box.height == pytest.approx(expected.height, abs=2)
    assert box.x == pytest.approx(50, abs=2)
    assert box.y + box.height == pytest.approx(0, abs=2)


def test_baseline_and_scale_options() -> None:
    fb = svg.FontBuilder(family="Offset")
    fb.glyph("x", svg.rect(0, 0, 50, 50), baseline=50, scale=10)
    box = svg.text("x", font_family=fb.typeface(), font_size=1000).to_path().bbox
    assert (round(box.y), round(box.height)) == (-500, 500)


def test_strokes_become_outline() -> None:
    fb = svg.FontBuilder(family="Stroke")
    fb.glyph("l", svg.path("M0 -700 V0", fill="none", stroke="black", stroke_width=100))
    assert fb.advance("l") == 100


def test_kerning_lands_in_gpos() -> None:
    font = _font(_letters())
    lookup = font["GPOS"].table.LookupList.Lookup[0].SubTable[0]
    assert lookup.Coverage.glyphs == ["A"]
    assert lookup.PairSet[0].PairValueRecord[0].Value1.XAdvance == -80
    with pytest.raises(KeyError):
        _letters().kern("A", "Z", -10)


def test_truetype_is_quadratic() -> None:
    font = _font(_letters(), ".ttf")
    assert "glyf" in font and "CFF " not in font
    assert font["glyf"]["o"].numberOfContours == 2


def test_icons_get_stable_private_use_points() -> None:
    fb = svg.FontBuilder(family="Icons")
    names = ["rocket", "star", "home", "bell"]
    chars = [fb.icon(name, svg.rect(0, 0, 24, 24 + index)) for index, name in enumerate(names)]
    assert [ord(c) for c in chars] == [0xE000, 0xE001, 0xE002, 0xE003]
    assert fb.icon("star", svg.circle(0, 0, 5)) == chars[1]
    assert list(fb.icons) == names
    cmap = _font(fb).getBestCmap()
    assert cmap[0xE000] == "rocket"


def test_icon_fills_the_em() -> None:
    fb = svg.FontBuilder(family="Fit")
    fb.icon("wide", svg.rect(10, 10, 40, 20))
    assert fb.advance("wide") == 1000
    box = svg.text(fb.icons["wide"], font_family=fb.typeface(), font_size=1000).to_path().bbox
    assert (round(box.x), round(box.width), round(box.height)) == (0, 1000, 500)
    assert round(box.y + box.height / 2) == -300


def test_css_and_cheatsheet(tmp_path: Path) -> None:
    fb = _letters()
    fb.icon("rocket", svg.builder.star(0, 0, 10))
    css = fb.save_css(tmp_path / "icons.css", font="Icons.woff2").read_text(encoding="utf-8")
    assert 'src: url("Icons.woff2") format("woff2")' in css
    assert r'.icon-rocket::before { content: "\e000"; }' in css
    assert "ic-rocket" in fb.css("Icons.ttf", prefix="ic")
    sheet = fb.cheatsheet(columns=2).to_string()
    for label in ("rocket", "U+E000", "U+0041", ">o<"):
        assert label in sheet


def test_save_picks_format_from_suffix(tmp_path: Path) -> None:
    fb = _letters()
    assert fb.save(tmp_path / "Hand.otf").read_bytes()[:4] == b"OTTO"
    assert fb.save(tmp_path / "Hand.woff").read_bytes()[:4] == b"wOFF"
    with pytest.raises(ValueError, match="unknown font format"):
        fb.save(tmp_path / "Hand.png")


def test_woff2_needs_brotli() -> None:
    try:
        import brotli  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError, match=r"pysvgwriter\[fonts\]"):
            _letters().to_bytes("woff2")
    else:
        assert _letters().to_bytes("woff2")[:4] == b"wOF2"
