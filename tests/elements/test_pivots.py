from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter import Point

CORNERS = {
    "center": (5, 2), "top": (5, 0), "bottom": (5, 4), "left": (0, 2), "right": (10, 2),
    "top_left": (0, 0), "top_right": (10, 0), "bottom_left": (0, 4), "bottom_right": (10, 4),
}


class TestNamedAnchor:
    @pytest.mark.parametrize(("name", "point"), CORNERS.items())
    def test_names_resolve_on_local_box(self, name: str, point: tuple[float, float]) -> None:
        r = svg.rect(0, 0, 10, 4)
        r.anchor = name
        assert r.anchor == Point(*point)

    def test_origin(self) -> None:
        r = svg.rect(3, 3, 10, 4, anchor="origin")
        assert r.anchor == Point(0, 0)

    def test_name_follows_edits(self) -> None:
        r = svg.rect(0, 0, 10, 4)
        r.anchor = "bottom"
        r.height = 8
        assert r.anchor == Point(5, 8)

    def test_name_moves_with_transform(self) -> None:
        r = svg.rect(0, 0, 10, 4).translate(100, 0)
        r.anchor = "bottom_right"
        assert r.position == Point(110, 4)

    def test_unknown_name_lists_valid(self) -> None:
        with pytest.raises(ValueError, match="top_left"):
            svg.rect(0, 0, 1, 1).anchor = "upper"

    def test_baseline_only_on_text(self) -> None:
        with pytest.raises(ValueError, match="baseline"):
            svg.rect(0, 0, 1, 1).anchor = "baseline"
        t = svg.Text("Hi", x=10, y=50, font_size=20)
        t.anchor = "baseline"
        assert t.anchor == Point(10, 50)

    def test_text_default_is_box_centre(self) -> None:
        t = svg.Text("Hi", x=10, y=50, font_size=20)
        assert t.anchor == t.local_bbox().center


class TestNamedAbout:
    @pytest.mark.parametrize("method", ["rotate", "scale", "skew"])
    def test_name_matches_point(self, method: str) -> None:
        arg = {"rotate": 30, "scale": 2, "skew": 20}[method]
        a = getattr(svg.rect(0, 0, 10, 4).translate(5, 5), method)(arg, about="bottom_left")
        b = getattr(svg.rect(0, 0, 10, 4).translate(5, 5), method)(arg, about=(5, 9))
        assert a.t == b.t

    def test_flip_about_name(self) -> None:
        assert svg.rect(0, 0, 10, 10).flip_x(about="left").bounds().x == -10

    def test_animation_preset_uses_local_point(self) -> None:
        bar = svg.rect(0, 0, 40, 10).translate(100, 100)
        bar.animate.rotate(90, about="bottom_left")
        assert bar.children[0].get("to") == "90 0 10"

    def test_animation_preset_rejects_unknown(self) -> None:
        with pytest.raises(ValueError, match="unknown pivot"):
            svg.rect(0, 0, 1, 1).animate.scale(2, about="nowhere")
