from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.model.pathdata import BBox


def test_rect_from_corners_center_and_square() -> None:
    assert svg.Rect.from_corners((30, 40), (10, 20)).bbox == (10, 20, 20, 20)
    assert svg.Rect.from_center((50, 50), (20, 10)).bbox == (40, 45, 20, 10)
    assert svg.Rect.square(10, center=(0, 0)).bbox == (-5, -5, 10, 10) and svg.Rect.square(4).bbox == (0, 0, 4, 4)


def test_ellipse_and_circle_from_bbox() -> None:
    box = BBox(0, 0, 40, 20)
    assert svg.Ellipse.from_bbox(box).bbox == box
    assert svg.Circle.from_bbox(box).bbox == (10, 0, 20, 20)


def test_length_reads_are_floats_unless_they_have_units() -> None:
    c = svg.Circle(5, 6, 7)
    assert (c.cx, c.cy, c.r) == (5.0, 6.0, 7.0) and all(isinstance(v, float) for v in (c.cx, c.cy, c.r))
    parsed = svg.parse('<rect x="3" width="2mm" height="50%"/>')
    assert parsed.x == 3.0 and str(parsed.width) == "2mm" and str(parsed.height) == "50%"
    assert svg.Rect().rx is None


def test_lowercase_aliases_carry_constructors() -> None:
    assert svg.rect.from_center((0, 0), (2, 2)).bbox == (-1, -1, 2, 2)


def test_detached_use_resolves_its_target() -> None:
    dot = svg.circle(0, 0, 2)
    use = svg.Use(dot, x=10)
    assert use.referenced() is dot and use.bounds() == (8, -2, 4, 4)
    assert use.to_path().exact_bbox() == (8, -2, 4, 4)


def test_rect_outline_has_no_redundant_closing_segment() -> None:
    assert str(svg.Rect(0, 0, 4, 3).local_outline()) == "M0 0 H4 V3 H0 Z"
    assert "A" in str(svg.Rect(0, 0, 4, 3, rx=1).local_outline())


def test_builder_extend_continues_from_the_current_point() -> None:
    from svgwriter.model.pathdata import PathBuilder

    b = PathBuilder().move_to(1, 1).extend("l2 0 L5 5").extend("M9 9 h1")
    assert str(b.build()) == "M1 1 l2 0 L5 5 M9 9 h1"


def test_points_after_close_restart_from_the_subpath_start() -> None:
    from svgwriter.model.pathdata import PathData

    pts = list(PathData("M10 10 L20 10 L20 20 Z L10 0").points())
    assert pts[-1] == (10, 0) and pts[-2] == (20, 20)


def test_small_fixes() -> None:
    from svgwriter.model.color import PaintKeyword
    from svgwriter.model.transform import Transform

    assert str(PaintKeyword.NONE) == "none"
    with pytest.raises(TypeError):
        hash(Transform.rotate(5))
    glow = svg.filters.glow(5)
    assert glow.get("x") == "-50%" and glow.get("width") is not None


class TestUnknownAttributeHints:
    def test_animation_and_behavior_presets_point_at_animate(self):
        with pytest.raises(AttributeError, match=r"fade_out is an animation; use element\.animate\.fade_out"):
            svg.text("A").fade_out()
        with pytest.raises(AttributeError, match=r"wiggle is a behavior; use element\.animate\.wiggle"):
            _ = svg.rect(0, 0, 1, 1).wiggle

    def test_close_matches_cover_methods_attributes_and_presets(self):
        with pytest.raises(AttributeError, match="did you mean 'animate.fade_out'"):
            _ = svg.text("A").fade_ot
        with pytest.raises(AttributeError, match="did you mean 'width'"):
            _ = svg.rect(0, 0, 1, 1).widht
