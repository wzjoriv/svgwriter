"""Emoji: one glyph per cluster, in colour where the format allows, never blank without saying so."""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal._constants import EMOJI_PROBE
from svgwriter._internal._render._rendering import renderable_copy
from svgwriter._internal._typography import _emoji
from svgwriter._internal._typography._fonts import color_font, font_for
from svgwriter.formats.export import export

ZWJ, VS16 = chr(0x200D), chr(0xFE0F)
SKIN = "\U0001f44d\U0001f3fd"
FAMILY = ZWJ.join([chr(0x1F468), chr(0x1F469), chr(0x1F467)])
KEYCAP = "1" + VS16 + chr(0x20E3)
HEART = chr(0x2764) + VS16
SMILE = "\U0001f600"
EMOJI = [SMILE, SKIN, FAMILY, KEYCAP, HEART]
LINE = "hi " + " ".join(EMOJI)
PLAIN = "Hello, wörld ✓"

pytestmark = pytest.mark.skipif(
    not color_font(font_for(EMOJI_PROBE, "sans-serif", 16).getTypeface()),
    reason="no colour emoji font installed (Segoe UI Emoji, Apple Color Emoji or fonts-noto-color-emoji)")


def _doc(text: str = LINE, **attributes: object) -> svg.Document:
    doc = svg.Document(400, 60)
    doc.text(text, x=10, y=40, font_size=28, **attributes)
    return doc


def _chroma(pixels: np.ndarray) -> float:
    """Largest spread between colour channels over the pixels that are drawn."""
    drawn = pixels[pixels[..., 3] > 0.5]
    return float((drawn[:, :3].max(axis=1) - drawn[:, :3].min(axis=1)).max()) if len(drawn) else 0.0


def _color_boxes(text: str) -> list[object]:
    return [box for box in svg.Text(text, x=0, y=20, font_size=20).layout() if box.color is not None]


def test_each_emoji_is_one_cluster() -> None:
    boxes = _color_boxes(LINE)
    assert [box.color.text for box in boxes] == EMOJI
    assert len(boxes[EMOJI.index(SKIN)].color.glyphs) == 1
    assert len(boxes[EMOJI.index(KEYCAP)].color.glyphs) == 1


def test_emoji_have_no_outline_and_plain_text_no_colour() -> None:
    assert not any(len(box.outline) for box in svg.Text(SKIN, x=0, y=20).layout())
    assert _color_boxes(PLAIN) == []


def test_png_draws_emoji_in_colour() -> None:
    pixels = _doc(SMILE).rasterize()
    assert _chroma(pixels) > 0.5


def test_png_keeps_transform_opacity_and_clip() -> None:
    doc = svg.Document(200, 100)
    text = doc.text(SMILE, x=100, y=60, font_size=40, opacity=0.5)
    text.matrix = svg.Matrix.translate(-80, 0)
    alpha = doc.rasterize()[..., 3]
    assert alpha[:, :60].max() == pytest.approx(0.5, abs=0.02)
    assert alpha[:, 80:].max() == 0
    doc.add(svg.Defs(svg.ClipPath(svg.Rect(150, 0, 50, 100), id="right")))
    text.attributes["clip-path"] = "url(#right)"
    assert doc.rasterize()[..., 3].max() == 0


def test_plain_text_pixels_unchanged_by_emoji_beside_it() -> None:
    both = svg.Document(400, 100)
    both.text(PLAIN, x=10, y=30, font_size=20)
    both.text(SMILE, x=10, y=80, font_size=20)
    alone = svg.Document(400, 100)
    alone.text(PLAIN, x=10, y=30, font_size=20)
    assert np.array_equal(both.rasterize()[:50], alone.rasterize()[:50])


def test_plain_text_render_tree_has_no_colour_layer() -> None:
    doc = _doc(PLAIN)
    copy = renderable_copy(doc.root, color_glyphs=True)
    assert not any(element.tag == "text" for element in copy.iter())


def test_pdf_draws_one_glyph_run_per_emoji(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[int]] = []
    original = _emoji.draw_glyphs

    def spy(canvas, font, glyphs, offsets, place, paint):  # type: ignore[no-untyped-def]
        calls.append(list(glyphs))
        original(canvas, font, glyphs, offsets, place, paint)

    monkeypatch.setattr(_emoji, "draw_glyphs", spy)
    assert export(_doc(SKIN), "pdf").startswith(b"%PDF")
    assert sorted(len(call) for call in calls) == [1, 2]


def test_eps_places_masked_images() -> None:
    eps = export(_doc(), "eps").decode("ascii")
    assert eps.count("/ImageType 3") == len(EMOJI)
    assert "%%LanguageLevel: 3" in eps


def test_tikz_draws_cells_and_keeps_text() -> None:
    tikz = export(_doc(), "tikz")
    plain = export(_doc("hi"), "tikz")
    assert tikz.count("\\path[") > plain.count("\\path[") + len(EMOJI)
    assert "{hi}" in tikz and SMILE not in tikz


@pytest.mark.parametrize("name", ["dxf", "hpgl"])
def test_outline_formats_warn(name: str) -> None:
    with pytest.warns(UserWarning, match="colour emoji"):
        export(_doc(), name)


def test_outline_formats_silent_without_emoji(recwarn: pytest.WarningsRecorder) -> None:
    export(_doc(PLAIN), "dxf")
    assert not [w for w in recwarn if "emoji" in str(w.message)]


def test_pptx_and_svg_keep_emoji_as_text() -> None:
    pptx = zipfile.ZipFile(io.BytesIO(export(_doc(), "pptx")))
    slides = "".join(pptx.read(name).decode("utf-8") for name in pptx.namelist() if name.startswith("ppt/slides/"))
    assert SKIN in slides and FAMILY in slides
    assert SKIN in export(_doc(), "svg")


def test_emoji_images_sit_on_the_baseline() -> None:
    images = _emoji.color_glyph_images(_doc(SMILE))
    assert len(images) == 1
    pixels, matrix = images[0]
    rows, columns = pixels.rgba().shape[:2]
    top, bottom = matrix.apply(0, 0).y, matrix.apply(columns, rows).y
    assert top < 40 < bottom + 10
