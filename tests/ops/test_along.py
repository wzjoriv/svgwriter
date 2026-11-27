import math

import pytest

import svgwriter as svg
from svgwriter.ops import frames, sample, segment


class TestPositions:
    def test_at_tangent_and_normal_by_fraction(self):
        line = svg.line(0, 0, 10, 0)
        assert line.at(0) == (0, 0) and line.at(0.5) == (5, 0) and line.at(2) == (10, 0)
        assert line.tangent_at(0.3) == (1, 0) and line.normal_at(0.3) == pytest.approx((0, -1))
        assert svg.circle(0, 0, 10).normal_at(0.1) == pytest.approx(svg.circle(0, 0, 10).at(0.1) / 10, abs=1e-6)

    def test_positions_follow_the_transform(self):
        moved = svg.line(0, 0, 10, 0).translate(5, 5)
        assert moved.at(1) == (15, 5)

    def test_sample_open_and_closed(self):
        assert svg.line(0, 0, 10, 0).sample(3) == [(0, 0), (5, 0), (10, 0)]
        square = sample(svg.rect(0, 0, 10, 10), 4)
        assert square == [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert sample("M0 0 L10 0", 1) == [(0, 0)]
        with pytest.raises(ValueError, match="at least one"):
            sample("M0 0 L10 0", 0)
        with pytest.raises(ValueError, match="zero length"):
            frames("M0 0", 2)


class TestBetween:
    def test_by_fraction_and_by_length(self):
        line = svg.line(0, 0, 10, 0, stroke="red")
        piece = line.between(0.2, 0.5)
        assert str(piece.d) == "M2 0 L5 0" and piece.get("stroke") == "red"
        assert str(line.between(1, 4, by="length").d) == "M1 0 L4 0"
        assert str(line.between(start=svg.px(3), by="length").d) == "M3 0 L10 0"

    def test_spans_subpaths_and_closes_whole_loops(self):
        assert str(segment("M0 0 L10 0 M0 5 L10 5", 5, 15)) == "M5 0 L10 0 M0 5 L5 5"
        assert str(segment("M0 0 H10 V10 H0 Z", 0, 40)).endswith("Z")

    def test_errors(self):
        line = svg.line(0, 0, 10, 0)
        with pytest.raises(ValueError, match="comes before"):
            line.between(0.8, 0.2)
        with pytest.raises(ValueError, match="by must be"):
            line.between(0, 1, by="percent")


class TestDistribute:
    def test_places_and_orients(self):
        dots = [svg.rect(-1, -1, 2, 2) for _ in range(3)]
        result = svg.distribute(dots, along=svg.polyline([(0, 0), (10, 0), (10, 10)]))
        assert result == dots
        assert [d.position for d in dots] == [(0, 0), (10, 0), (10, 10)]
        assert dots[2].matrix.decompose()[2] == pytest.approx(90)

    def test_without_orientation_and_on_closed_paths(self):
        marks = svg.distribute([svg.circle(0, 0, 1) for _ in range(4)], along=svg.circle(0, 0, 10), orient=False)
        assert all(math.isclose(abs(m.position), 10, rel_tol=1e-4) for m in marks)
        assert len({(round(m.position.x), round(m.position.y)) for m in marks}) == 4
        assert svg.distribute([], along="M0 0 L1 0") == []
