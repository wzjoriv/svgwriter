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
        svg.text_effects.fire(line[0:4])
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
    @pytest.mark.parametrize("name", svg.text_effects.__all__)
    def test_animates_unless_asked_not_to(self, name: str) -> None:
        still_doc, still = _line()
        moving_doc, moving = _line()
        getattr(svg.text_effects, name)(still, animate=False)
        getattr(svg.text_effects, name)(moving)
        assert "<animate" not in still_doc.to_string()
        assert "<animate" in moving_doc.to_string()

    def test_frames_differ_over_time(self) -> None:
        doc, line = _line()
        svg.text_effects.glitch(line)
        first, later = np.asarray(doc.at(0).rasterize()), np.asarray(doc.at(0.5).rasterize())
        assert (first != later).any()

    def test_user_effect_works_on_ranges(self) -> None:
        @svg.preset.text_effect
        def ink(text: svg.Text, *, color: str = "navy") -> None:
            text.fill = color

        try:
            _, line = _line()
            assert line[0:4].effect("ink", color="red").get("fill") == "red"
        finally:
            svg.preset.unregister("text_effect", "ink")
