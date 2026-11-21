import pytest

import svgwriter as svg
from svgwriter.ops import Corner, corners, round_corners


class TestCorners:
    def test_vertices_and_turning_angles(self):
        found = svg.polyline([(0, 0), (10, 0), (10, 10), (0, 10)]).corners()
        assert [c.index for c in found] == [1, 2] and all(c.angle.degrees == pytest.approx(90) for c in found)
        assert corners("M0 0 L10 0 L0 1")[0].angle.degrees == pytest.approx(174.29, abs=0.01)
        assert corners("M0 0 L10 0 L20 -10")[0].angle.degrees == pytest.approx(-45)

    def test_smooth_outlines_and_numbering_across_subpaths(self):
        assert svg.circle(0, 0, 5).corners() == [] and svg.ellipse(0, 0, 5, 2).corners() == []
        found = corners("M0 0 H10 V10 H0 Z M20 0 L30 0 L30 10")
        assert [c.index for c in found] == [0, 1, 2, 3, 5]
        assert isinstance(found[0], Corner) and found[4].point == (30, 0)


class TestRounding:
    def test_arcs_between_straight_sides(self):
        assert str(round_corners("M0 0 H10 V10", 2)) == "M0 0 L8 0 A2 2 0 0 1 10 2 L10 10"
        rounded = svg.rect(0, 0, 10, 10).round_corners(2)
        assert rounded.tag == "path" and rounded.corners() == []
        assert rounded.exact_bbox().width == pytest.approx(10)

    def test_selection_by_predicate_indices_and_single_corner(self):
        square = svg.rect(0, 0, 10, 10, fill="red")
        assert [c.point for c in square.round_corners(1, where=lambda c: c.index % 2 == 0).corners()] == [(10, 0), (0, 10)]
        assert [c.point for c in square.round_corners(1, where=[0]).corners()] == [(10, 0), (10, 10), (0, 10)]
        single = square.round_corner(2, 3)
        assert len(single.corners()) == 3 and single.get("fill") == "red"
        with pytest.raises(ValueError, match="not corners"):
            square.round_corners(1, where=[7])

    def test_quadratic_fillets_and_short_sides(self):
        quad = round_corners("M0 0 H10 V10", 2, fillet="quad")
        assert str(quad) == "M0 0 L8 0 Q10 0 10 2 L10 10"
        clipped = round_corners("M0 0 H2 V2 H0 Z", 5)
        assert str(clipped).count("A1 1") == 4

    def test_lengths_and_curved_neighbours(self):
        assert str(svg.polyline([(0, 0), (10, 0), (10, 10)]).round_corners(svg.px(2)).d).startswith("M0 0 L8 0 A2 2")
        bent = round_corners("M0 0 Q5 -5 10 0 L10 10", 1)
        assert "C" in str(bent) and corners(bent) == []
