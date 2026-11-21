from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg


def _line() -> tuple[svg.Document, svg.Text]:
    doc = svg.Document(300, 60)
    return doc, doc.text("into the cold night", x=10, y=40, font_size=24)


class TestRanges:
    def test_range_moves_onto_a_layer_above(self) -> None:
        doc, line = _line()
        layer = line[9:13].effect("ice")
        assert doc.root.children.index(layer) == doc.root.children.index(line) + 1
        assert line.characters == layer.characters == "into the cold night"
        shown = ["".join(map(str, span.children)) for span in line.find_all(svg.TSpan)
                 if span.get("visibility") == "hidden"]
        assert shown == ["cold"]

    def test_stays_text(self) -> None:
        doc, line = _line()
        svg.effects.fire(line[0:4])
        assert doc.root.find(svg.Path) is None and len(doc.root.find_all(svg.Text)) == 2

    def test_effects_on_two_ranges(self) -> None:
        doc, line = _line()
        line[0:4].effect("smoke")
        line[9:13].effect("snow")
        assert len(doc.root.find_all(svg.Text)) == 3

    def test_effect_paint_wins_over_a_role(self) -> None:
        doc, line = _line()
        line.as_role("text")
        layer = line[9:13].effect("metal")
        assert not layer.has("fill") and str(layer.style["fill"]).startswith("url(")

    def test_unplaced_range_explains(self) -> None:
        with pytest.raises(ValueError, match="add the text to a document"):
            svg.text("loose", x=0, y=0)[0:2].effect("fire")

    def test_unknown_effect_suggests(self) -> None:
        _, line = _line()
        with pytest.raises(KeyError, match="did you mean 'fire'"):
            line.effect("fir")

    def test_ids_are_not_duplicated(self) -> None:
        doc = svg.Document(300, 60)
        line = doc.text("Hello world", x=0, y=30, id="greeting")
        layer = line[6:11].effect("neon")
        assert line.id == "greeting" and layer.id != "greeting"


class TestAnimation:
    @pytest.mark.parametrize("name", svg.effects.__all__)
    def test_animates_unless_asked_not_to(self, name: str) -> None:
        still_doc, still = _line()
        moving_doc, moving = _line()
        getattr(svg.effects, name)(still, animate=False)
        getattr(svg.effects, name)(moving)
        assert "<animate" not in still_doc.to_string()
        assert "<animate" in moving_doc.to_string()

    def test_frames_differ_over_time(self) -> None:
        doc, line = _line()
        svg.effects.glitch(line)
        first, later = np.asarray(doc.at(0).rasterize()), np.asarray(doc.at(0.5).rasterize())
        assert (first != later).any()

    def test_user_effect_works_on_ranges(self) -> None:
        @svg.preset.effect
        def ink(text: svg.Text, *, color: str = "navy") -> None:
            text.fill = color

        try:
            _, line = _line()
            assert line[0:4].effect("ink", color="red").get("fill") == "red"
        finally:
            svg.preset.effect.unregister("ink")


EFFECT_NAMES = ("fire", "ice", "smoke", "metal", "wind", "snow", "neon", "glitch")


class TestAnyElement:
    @pytest.mark.parametrize("name", EFFECT_NAMES)
    def test_shapes_groups_and_images(self, name: str) -> None:
        doc = svg.Document(200, 120)
        targets = [doc.rect(10, 10, 60, 30), doc.circle(120, 30, 20), doc.group(), doc.add(svg.Image(np.ones((4, 4, 3))))]
        targets[2].add(svg.circle(40, 90, 10))
        for target in targets:
            assert target.effect(name) is target and target.get("filter") is not None
        assert doc.rasterize(scale=0.5).shape == (60, 100, 4)

    def test_sized_to_the_bounding_box(self) -> None:
        small = svg.effects.neon(svg.circle(0, 0, 10), animate=False).get("filter").element
        large = svg.effects.neon(svg.circle(0, 0, 40), animate=False).get("filter").element
        assert large.get("width") == pytest.approx(4 * small.get("width"))
        blurs = [child.get("stdDeviation") for child in large if child.tag == "feGaussianBlur"]
        assert blurs == [4 * child.get("stdDeviation") for child in small if child.tag == "feGaussianBlur"]

    def test_text_keeps_its_glyph_sizing(self) -> None:
        tall = svg.text("Wide words here", x=0, y=40, font_size=32)
        area = svg.effects.fire(tall).get("filter").element
        box = tall.visible_bbox()
        assert area.get("height") == pytest.approx(round(box.height * 2.8, 3), abs=0.01)

    def test_not_an_element(self) -> None:
        with pytest.raises(TypeError, match="effects apply to an element or a range of a text"):
            svg.effects.fire("hot")

    def test_unknown_name_suggests(self) -> None:
        with pytest.raises(svg.UnknownNameError, match="did you mean 'neon'"):
            svg.rect(0, 0, 1, 1).effect("nein")
