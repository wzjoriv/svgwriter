import math

import pytest

import svgwriter as svg
from svgwriter.model.elements.structure import Pixels


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
        with pytest.raises(ValueError, match="relative"):
            svg.em(2) + svg.inch(1)

    def test_unit_factories_call_or_multiply(self):
        assert svg.mm(5) == 5 * svg.mm

    @pytest.mark.parametrize(("text", "expected"), [
        ("2 metres", "2000mm"), ("1ft", "12in"), ("3Q", "3Q"), ("3q", "3Q"), ("2 Inches", "2in"),
        ("4 pixels", "4px"), ("5 points", "5pt"), ("1 centimetre", "1cm"), ("7 millimeters", "7mm"), ("10%", "10%"),
    ])
    def test_spelled_units_parse_and_write_canonical_suffixes(self, text, expected):
        assert str(svg.Length.parse(text)) == expected

    def test_lowercase_factories_and_input_only_units(self):
        assert svg.length(1.5, "meters") == svg.mm(1500) == svg.m(1.5)
        assert svg.length(2, "ft") == svg.ft(2) == svg.inch(24)
        assert svg.q(4).to("mm").value == pytest.approx(1) and svg.length(3) == svg.Length(3)
        with pytest.raises(ValueError, match="unknown length unit"):
            svg.length(1, "cubit")
        with pytest.raises(ValueError, match="unknown length unit"):
            svg.Length.parse("3 parsecs")


    def test_a_unit_is_one_of_itself(self):
        assert svg.inch == svg.Length(1, "in") and svg.turn == svg.deg(360)
        doc = svg.Document(width=400, height=300)
        assert str(doc.rect(width=2 * svg.inch, height=svg.inch).attributes["height"]) == "1in"

    @pytest.mark.parametrize(("unit", "text"), [
        (svg.km, "1000000mm"), (svg.um, "0.001mm"), (svg.nmi, "1852000mm"), (svg.yd, "36in"),
        (svg.mi, "63360in"), (svg.furlong, "7920in"), (svg.mil, "0.001in"),
    ])
    def test_units_svg_has_no_name_for_are_written_in_svg_units(self, unit, text):
        assert str(unit(1)) == str(1 * unit) == text

    def test_spelled_out_units(self):
        assert svg.length(2, "miles") == svg.mi(2) and svg.length(1, "µm") == svg.um(1)
        assert svg.length(1, "nautical mile") == svg.nmi(1) and svg.length(3, "thou") == svg.mil(3)


class TestAngles:
    def test_conversions_and_mixing(self):
        assert float(svg.turn(0.25)) == 90 and svg.Angle.parse("100grad").degrees == pytest.approx(90)
        assert (svg.rad(math.pi) + 30).to("deg").value == pytest.approx(210)
        assert svg.deg(30) < svg.rad(1) and svg.turn(1) / svg.deg(90) == pytest.approx(4)

    @pytest.mark.parametrize(("unit", "expected"), [
        ("degree", "deg"), ("degrees", "deg"), ("radian", "rad"), ("radians", "rad"), ("gon", "grad"),
        ("gradian", "grad"), ("gradians", "grad"), ("turns", "turn"), ("TURN", "turn"),
    ])
    def test_spelled_units_construct_canonical_angles(self, unit, expected):
        assert svg.angle(1, unit).unit == expected and svg.Angle.parse(f"1 {unit}").unit == expected

    def test_wrap_diff_and_lerp(self):
        assert svg.deg(-90).wrap() == svg.deg(270) and svg.turn(2.5).wrap().value == pytest.approx(0.5)
        assert svg.deg(350).diff(10).degrees == pytest.approx(20)
        assert svg.deg(350).diff(10, ccw=True).degrees == pytest.approx(-340)
        assert svg.deg(10).diff(350, ccw=False).degrees == pytest.approx(340)
        assert svg.deg(350).lerp(10, 0.5).wrap().degrees == pytest.approx(0)
        assert svg.deg(0).lerp(90, 0.5, ccw=True).degrees == pytest.approx(-135)

    def test_trigonometry_clamp_and_arclength(self):
        assert svg.deg(30).sin() == pytest.approx(0.5) and svg.turn(0.5).cos() == pytest.approx(-1)
        assert svg.deg(45).tan() == pytest.approx(1)
        assert svg.deg(100).clamp(0, 90) == svg.deg(90) and svg.deg(-5).clamp(0, 90) == svg.deg(0)
        assert svg.deg(5).clamp(350, 20, circular=True) == svg.deg(5)
        assert svg.deg(100).clamp(350, 20, circular=True).degrees == pytest.approx(20)
        assert svg.deg(300).clamp(350, 20, circular=True).degrees == pytest.approx(350)
        assert svg.rad(2).arclength(svg.mm(3)) == svg.mm(6) and svg.deg(-180).arclength(1).value == pytest.approx(math.pi)

    def test_rotations_accept_angles(self):
        assert str(svg.rect(0, 0, 4, 2).rotate(svg.rad(math.pi / 2)).t) == "rotate(90 2 1)"
        assert str((svg.rect(0, 0, 4, 2) @ svg.turn(0.25)).t) == "rotate(90 2 1)"


def test_physical_documents_and_dpi():
    page = svg.Document(1 * svg.inch, 0.5 * svg.inch)
    assert page.root.view_box.width == 1 and page.root.get("width") == svg.inch(1)
    assert Pixels.decode(page.export("png", dpi=300)).shape == (150, 300)
    assert Pixels.decode(svg.Document(210 * svg.mm, 297 * svg.mm).export("png")).shape == (1123, 794)
