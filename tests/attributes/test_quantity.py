import math

import pytest

import svgwriter as svg
from svgwriter.model.attributes import Quantity


class TestDimensions:
    def test_products_carry_exponents(self):
        area = svg.mm(3) * svg.mm(2)
        assert isinstance(area, Quantity) and (area.length, area.angle) == (2, 0) and str(area) == "6mm²"
        assert (svg.mm(3) * svg.deg(2)).dimension == "length·angle"
        assert (svg.deg(90) / svg.mm(5)).dimension == "length⁻¹·angle"
        assert (2 / svg.mm(4)).dimension == "length⁻¹" and (svg.inch(2) ** 3).dimension == "length³"

    def test_cancelling_dimensions_give_lengths_angles_and_numbers(self):
        assert svg.mm(3) * svg.mm(2) / svg.mm(4) == svg.mm(1.5)
        assert svg.mm(6) / svg.mm(3) == 2.0 and svg.inch(1) / svg.mm(25.4) == pytest.approx(1)
        assert (svg.deg(30) * svg.mm(2) / svg.mm(1)).degrees == pytest.approx(60)
        speed = svg.deg(90) / svg.mm(5)
        assert (speed * svg.mm(10)).degrees == pytest.approx(180)
        assert svg.mm(2) * svg.mm(3) / (svg.mm(1) * svg.mm(1)) == pytest.approx(6)

    def test_sums_need_matching_dimensions(self):
        total = svg.mm(1) * svg.mm(1) + svg.cm(1) * svg.cm(1)
        assert str(total) == "101mm²" and svg.mm(2) * svg.mm(2) > svg.mm(1) * svg.mm(3)
        with pytest.raises(TypeError, match="cannot add length² and length"):
            svg.mm(1) * svg.mm(1) + svg.mm(1)

    def test_relative_lengths_do_not_multiply(self):
        with pytest.raises(ValueError, match="em lengths need"):
            svg.em(2) * svg.mm(1)
        assert svg.em(4) / svg.em(2) == 2 and svg.em(2) * 3 == svg.em(6)

    def test_polar_point(self):
        point = svg.px(2) @ svg.deg(90)
        assert point.x == pytest.approx(0) and point.y == pytest.approx(2)
        assert (svg.inch(1) @ 0) == (96, 0) and (svg.mm(1) @ svg.rad(math.pi)).x == pytest.approx(-96 / 25.4)


class TestAssignmentChecks:
    def test_attribute_errors_name_the_attribute_and_dimension(self):
        rect = svg.rect(0, 0, 1, 1)
        with pytest.raises(TypeError, match="width needs a length, got length²"):
            rect.width = svg.mm(3) * svg.mm(2)
        with pytest.raises(TypeError, match="x needs a length, got angle"):
            rect.set("x", svg.deg(4))
        with pytest.raises(TypeError, match="rotate needs an angle, got length"):
            svg.text("a", rotate=svg.mm(2))
        rect.width = svg.mm(6) * svg.mm(2) / svg.mm(4)
        assert rect.get("width") == svg.mm(3)

    def test_parsing_refuses_the_wrong_dimension(self):
        with pytest.raises(TypeError, match="needs a length, got angle"):
            svg.Length.parse(svg.deg(3))
        with pytest.raises(TypeError, match="needs an angle, got length"):
            svg.Angle.parse(svg.mm(3))
        with pytest.raises(TypeError, match="needs an angle, got length·angle"):
            svg.rect(0, 0, 1, 1).rotate(svg.mm(1) * svg.deg(1))


class TestEquality:
    def test_user_unit_lengths_equal_numbers(self):
        assert svg.Length(320) == 320 and hash(svg.Length(320)) == hash(320)
        assert {svg.Length(5): "a"}[5] == "a"

    def test_absolute_lengths_compare_physically(self):
        assert svg.inch(1) == 96 and svg.inch(1) == svg.mm(25.4) and hash(svg.inch(1)) == hash(96)
        assert svg.mm(1) != 1

    def test_relative_lengths_only_equal_themselves(self):
        assert svg.Length(1, "em") == svg.Length(1, "em") and svg.Length(1, "em") != 16

    def test_angles_and_quantities_follow_numbers(self):
        assert svg.deg(180) == svg.rad(math.pi) and svg.deg(90) == 90 and hash(svg.deg(90)) == hash(90)
        assert svg.mm(2) * svg.mm(3) == svg.mm(3) * svg.mm(2) and svg.mm(2) * svg.mm(3) != 6
