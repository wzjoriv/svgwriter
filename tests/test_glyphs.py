from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.ops.text import layout_glyphs

FONT = "Arial, DejaVu Sans, Liberation Sans, sans-serif"


def text(content: str = "Hello", **kwargs) -> svg.Text:
    return svg.Text(content, x=10, y=40, font_size=30, font_family=FONT, **kwargs)


class TestLayout:
    def test_per_character_lists(self) -> None:
        boxes = layout_glyphs("abc", FONT, 20, x=[0, 50], dx=[0, 0, 5], rotate=[10])
        assert boxes[1].x == 50 and boxes[2].x == pytest.approx(50 + boxes[1].advance + 5)
        assert [b.angle for b in boxes] == [10, 10, 10]

    def test_anchor_middle(self) -> None:
        boxes = layout_glyphs("ab", FONT, 20, x=[100], anchor="middle")
        width = boxes[-1].x + boxes[-1].advance - boxes[0].x
        assert boxes[0].x == pytest.approx(100 - width / 2)


class TestIndexing:
    def test_len_iter_getitem(self) -> None:
        t = text()
        assert len(t) == 5 and [g.char for g in t] == list("Hello") and t[-1].char == "o"
        with pytest.raises(IndexError, match="5 characters"):
            _ = t[5]

    def test_children_still_hold_runs(self) -> None:
        t = svg.Text("ab")
        t.span("cd", fill="red")
        assert t.characters == "abcd" and len(t.children) == 2 and len(t) == 4

    def test_translate_moves_only_that_glyph(self) -> None:
        t = text()
        before = [g.position for g in t]
        t[2].translate(0, -10)
        after = [g.position for g in t]
        assert after[2].y == before[2].y - 10
        others = [c for i, p in enumerate(after) if i != 2 for c in p]
        assert others == pytest.approx([c for i, p in enumerate(before) if i != 2 for c in p])
        assert 'dy="0 0 -10 10"' in str(t)

    def test_translate_last_and_undo_cleans_up(self) -> None:
        t = text()
        t[-1].translate(5)
        assert t.dx == (0, 0, 0, 0, 5)
        t[-1].translate(-5)
        assert not t.has("dx")

    def test_rotate_only_one(self) -> None:
        t = text()
        t[1].rotate(45)
        assert [g.angle for g in t] == [0, 45, 0, 0, 0] and t.rotate_ == (0, 45, 0)
        t[1].rotate(-45)
        assert not t.has("rotate")

    def test_rotate_respects_repeating_last_value(self) -> None:
        t = text(rotate=10)
        t[0].rotate(5)
        assert [g.angle for g in t] == [15, 10, 10, 10, 10]

    def test_scale_points_to_glyphs(self) -> None:
        with pytest.raises(TypeError, match=r"text.glyphs\(\)\[3\]"):
            text()[3].scale(1.5)

    def test_outline_follows_glyph_edits(self) -> None:
        t = text()
        box = t.exact_bbox()
        t[0].translate(0, -20)
        assert t.exact_bbox().y < box.y - 15

    def test_glyph_bounds_and_to_path(self) -> None:
        t = text(fill="navy").translate(100, 0)
        b = t[0].bounds()
        assert b is not None and b.x > 100
        p = t[0].to_path()
        assert p.get("fill") is not None and p.exact_bbox() == pytest.approx(tuple(b), abs=0.5)


class TestGlyphGroup:
    def test_one_path_per_character_aligned(self) -> None:
        t = text("a b", fill="red").rotate(5)
        g = t.glyphs()
        assert len(g) == 3 and len(g[1].d) == 0 and str(g.t) == str(t.t)
        assert len(t.glyphs(skip_blank=True)) == 2

    def test_glyphs_transform_freely(self) -> None:
        g = text().glyphs()
        g[3].scale(1.5)
        assert g[3].bounds().width > text().glyphs()[3].bounds().width * 1.4

    def test_rendered_text_follows_edits(self) -> None:
        doc = svg.Document(200, 60)
        t = doc.add(text())
        plain = svg.ops.rasterize(doc).copy()
        t[0].translate(0, -15)
        assert (svg.ops.rasterize(doc) != plain).any()
