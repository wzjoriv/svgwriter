import math

import pytest

import svgwriter as svg
from svgwriter.elements.structure import Pixels


class TestLengths:
    def test_mixed_absolute_units_keep_the_left_unit(self):
        a, b = svg.inch(5), 7 * svg.mm
        assert str(a + b) == "5.2756in" and str(a - b) == "4.7244in"
        assert (a - b).to("mm").value == pytest.approx(120)
        assert str(svg.inch(8) - 96) == "7in"

    def test_numbers_are_user_units_on_either_side(self):
        assert (8 - svg.inch(1)).to("px").value == pytest.approx(-88)
        assert (svg.mm(10) + 0).value == 10

    def test_ratios_comparisons_and_errors(self):
        assert svg.inch(1) / svg.mm(25.4) == pytest.approx(1)
        assert svg.inch(1) > 90 * svg.px and svg.cm(1) < svg.inch(1)
        with pytest.raises(TypeError, match="area"):
            svg.inch(5) * svg.mm(7)
        with pytest.raises(ValueError, match="relative"):
            svg.em(2) + svg.inch(1)

    def test_unit_factories_call_or_multiply(self):
        assert svg.mm(5) == 5 * svg.mm


class TestAngles:
    def test_conversions_and_mixing(self):
        assert float(svg.turn(0.25)) == 90 and svg.Angle.parse("100grad").degrees == pytest.approx(90)
        assert (svg.rad(math.pi) + 30).to("deg").value == pytest.approx(210)
        assert svg.deg(30) < svg.rad(1) and svg.turn(1) / svg.deg(90) == pytest.approx(4)

    def test_rotations_accept_angles(self):
        assert str(svg.rect(0, 0, 4, 2).rotate(svg.rad(math.pi / 2)).t) == "rotate(90 2 1)"
        assert str((svg.rect(0, 0, 4, 2) @ svg.turn(0.25)).t) == "rotate(90 2 1)"


def test_physical_documents_and_dpi():
    page = svg.Document(1 * svg.inch, 0.5 * svg.inch)
    assert page.root.view_box.width == 1 and page.root.get("width") == svg.inch(1)
    assert Pixels.decode(page.export("png", dpi=300)).shape == (150, 300)
    assert Pixels.decode(svg.Document(210 * svg.mm, 297 * svg.mm).export("png")).shape == (1123, 794)
