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


class TestTSpans:
    def test_tspan_font_and_position_apply(self) -> None:
        t = svg.Text("ab", x=0, y=20, font_size=10, font_family=FONT)
        t.span("cd", font_size=40, dy=5)
        boxes = t.layout()
        assert [b.char for b in boxes] == list("abcd") and boxes[2].y == 25 and boxes[3].y == 25
        assert boxes[2].advance > 2 * boxes[0].advance

    def test_innermost_positioning_wins(self) -> None:
        t = svg.Text(x=[0, 100], y=20, font_family=FONT)
        t.span("ab", x=[50])
        assert [b.x for b in t.layout()][:1] == [50]

    def test_whitespace_collapses_across_runs(self) -> None:
        t = svg.Text("\n   a  ", font_family=FONT)
        t.span("  b\t")
        assert t.characters == "a b"

    def test_preserve(self) -> None:
        t = svg.Text(" a\tb ", xml_space="preserve")
        assert t.characters == " a b "

    def test_runs_and_glyph_styles_follow_tspans(self) -> None:
        t = svg.Text("ab", x=0, y=20, fill="black", font_family=FONT)
        t.span("cd", fill="red")
        runs = t.runs()
        assert len(runs) == 2 and str(runs[1].get("fill")) == "red" and str(runs[0].get("fill")) == "black"
        assert str(t.glyphs()[3].get("fill")) == "red"

    def test_tspan_colour_renders(self) -> None:
        doc = svg.Document(120, 40)
        t = doc.text("aa", x=0, y=30, font_size=30, fill="black", font_family=FONT)
        t.span("WW", fill="red")
        pixels = svg.ops.rasterize(doc, background="white")
        reds = (pixels[..., 0] > 0.8) & (pixels[..., 1] < 0.2)
        assert reds[:, 40:].any() and not reds[:, :25].any()


class TestRanges:
    def test_slice_basics(self) -> None:
        t = text("Hello world")
        rng = t[6:]
        assert rng.chars == "world" and len(rng) == 5 and [g.char for g in rng] == list("world")
        with pytest.raises(ValueError, match="contiguous"):
            _ = t[::2]

    def test_translate_range_moves_only_it(self) -> None:
        t = text("Hello world")
        before = [g.position.y for g in t]
        t[6:11].translate(0, -5)
        after = [g.position.y for g in t]
        assert after[6:] == [y - 5 for y in before[6:]] and after[:6] == before[:6]
        t[0:2].translate(3)
        assert t[2].position.x == pytest.approx(text("Hello world")[2].position.x)

    def test_rotate_range(self) -> None:
        t = text()
        t[1:3].rotate(30)
        assert [g.angle for g in t] == [0, 30, 30, 0, 0]

    def test_styling_wraps_in_tspan_and_keeps_characters(self) -> None:
        t = text("Hello world")
        t[6:11].fill = "red"
        assert t.characters == "Hello world" and isinstance(t.children[1], svg.TSpan)
        assert str(t.children[1].get("fill")) == "red" and t[6].char == "w"
        span = t[0:5].wrap(font_weight="bold")
        assert span.text_content == "Hello" and t.children[0] is span

    def test_wrap_errors(self) -> None:
        t = text("Hello world")
        t[6:11].fill = "red"
        with pytest.raises(ValueError, match="crosses"):
            t[3:8].fill = "blue"
        with pytest.raises(ValueError, match="empty"):
            t[2:2].wrap(fill="red")
        with pytest.raises(AttributeError):
            t[0:2].nonsense = 1

    def test_range_bounds_and_path(self) -> None:
        t = text("Hello world")
        b = t[6:].bounds()
        assert b is not None and b.x > t[0:5].bounds().x + 20
        assert t[6:].to_path().exact_bbox() == pytest.approx(tuple(b), abs=0.5)

    def test_range_scale_hint(self) -> None:
        with pytest.raises(TypeError, match=r"glyphs\(\)\[1:3\]"):
            text()[1:3].scale(2)


class TestGraphemeClusters:
    def test_combining_marks_emoji_and_flags_are_one_character(self) -> None:
        family = "\U0001f469‍\U0001f469‍\U0001f467"
        flag = "\U0001f1fa\U0001f1f8"
        t = svg.text(f"é{family}{flag}1️⃣!", x=0, y=20)
        assert [c.char for c in t] == ["é", family, flag, "1️⃣", "!"]
        assert len(t) == 5 and t[1].index == 1 and t[-1].char == "!"
        assert t[1:3].chars == family + flag

    def test_two_flags_split_between_pairs(self) -> None:
        t = svg.text("\U0001f1fa\U0001f1f8\U0001f1eb\U0001f1f7", x=0, y=10)
        assert len(t) == 2

    def test_cluster_handles_edit_the_code_point_lists(self) -> None:
        t = svg.text("éx", x=0, y=10)
        t[1].translate(5, 0)
        assert t.get("dx") is not None and len(t) == 2
