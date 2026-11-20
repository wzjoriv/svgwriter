from __future__ import annotations

import math

import pytest

import svgwriter as svg
from svgwriter import builder
from tests.conftest import wellformed


def valid(element: svg.Path) -> None:
    wellformed(str(element))
    assert str(svg.Path(str(element.d)).d) == str(element.d)
    assert len(element.d) > 1


class TestRegularPolygon:
    def test_sharp_polygon_is_a_polygon(self) -> None:
        hexagon = builder.regular_polygon(10, 20, 5, 6, fill="red")
        assert hexagon.tag == "polygon" and len(hexagon.points) == 6
        assert hexagon.get("fill") == "red"
        assert hexagon.bbox.y == pytest.approx(15)

    def test_rotation_moves_the_first_corner(self) -> None:
        flat = builder.regular_polygon(0, 0, 10, 4, rotation=45)
        assert flat.bbox.width == pytest.approx(10 * math.sqrt(2))
        assert builder.regular_polygon(0, 0, 10, 4).bbox.width == pytest.approx(20)

    def test_rounded_corners_become_a_path_inside_the_sharp_outline(self) -> None:
        sharp = builder.regular_polygon(0, 0, 20, 5)
        rounded = builder.regular_polygon(0, 0, 20, 5, corner_radius=6, stroke="black")
        valid(rounded)
        assert rounded.tag == "path" and rounded.get("stroke") == "black"
        assert rounded.bbox.height < sharp.bbox.height
        assert str(rounded.d).count("A") == 5

    def test_oversized_radius_still_fits(self) -> None:
        box = builder.regular_polygon(0, 0, 20, 3, corner_radius=500).bbox
        assert box.width <= 40

    def test_rejects_too_few_sides(self) -> None:
        with pytest.raises(ValueError):
            builder.regular_polygon(0, 0, 5, 2)

    def test_booleans(self) -> None:
        a = builder.regular_polygon(0, 0, 20, 6, corner_radius=4)
        b = builder.regular_polygon(10, 0, 20, 6, corner_radius=4)
        assert (a & b).bbox.width < a.bbox.width
        assert (a | b).bbox.width > a.bbox.width
        assert (a - b).bbox.width < a.bbox.width


class TestStarCorners:
    def test_default_is_still_a_polygon(self) -> None:
        assert builder.star(0, 0, 10).tag == "polygon"

    def test_rounded_star_is_a_closed_path(self) -> None:
        star = builder.star(0, 0, 40, corner_radius=5, fill="gold")
        valid(star)
        assert star.tag == "path" and star.get("fill") == "gold"
        assert str(star.d).count("A") == 10
        assert str(star.d).endswith("Z")
        assert star.bbox.height < builder.star(0, 0, 40).bbox.height

    def test_four_pointed_star_rounds_concave_notches(self) -> None:
        star = builder.star(0, 0, 30, inner=8, points=4, corner_radius=2)
        valid(star)
        assert str(star.d).count("A") == 8


class TestHeart:
    def test_box(self) -> None:
        box = builder.heart(50, 40, 60).bbox
        assert box.width == pytest.approx(60)
        assert box.height == pytest.approx(57)
        assert box.x + box.width / 2 == pytest.approx(50)
        assert box.y + box.height / 2 == pytest.approx(40)

    def test_closed_symmetric_curves(self) -> None:
        heart = builder.heart(0, 0, 10, fill="red")
        valid(heart)
        assert str(heart.d).count("C") == 6
        assert str(heart.d).endswith("Z")
        assert heart.get("fill") == "red"

    def test_transforms_and_booleans(self) -> None:
        left, right = builder.heart(0, 0, 40), builder.heart(30, 0, 40)
        assert (left & right).bbox.width < 40
        assert (left | right).bbox.width > 60
        moved = builder.heart(0, 0, 40).place(10, 10)
        assert moved.bbox.width == pytest.approx(40)


class TestCallout:
    @pytest.mark.parametrize("tail", [(20, 70), (20, -30), (-30, 20), (130, 20)])
    def test_tail_reaches_the_point_from_the_nearest_side(self, tail: tuple[float, float]) -> None:
        bubble = builder.callout(0, 0, 100, 40, tail=tail, fill="white")
        valid(bubble)
        box = bubble.bbox
        assert (box.x, box.y, box.x + box.width, box.y + box.height) == pytest.approx(
            (min(0, tail[0]), min(0, tail[1]), max(100, tail[0]), max(40, tail[1]))
        )

    def test_rounded_body_and_sharp_tail(self) -> None:
        bubble = builder.callout(0, 0, 100, 40, tail=(30, 60), corner_radius=10)
        assert str(bubble.d).count("A") == 4
        assert str(builder.callout(0, 0, 100, 40, tail=(30, 60), corner_radius=0).d).count("A") == 0

    def test_tail_base_stays_clear_of_the_rounded_corners(self) -> None:
        bubble = builder.callout(0, 0, 100, 40, tail=(-50, 90), corner_radius=10)
        base = [point for point in bubble.d.points() if point[1] == 40 and point[0] != -50] if hasattr(bubble.d, "points") else []
        assert all(point[0] >= 10 for point in base)
        assert bubble.bbox.x == pytest.approx(-50)

    def test_booleans(self) -> None:
        bubble = builder.callout(0, 0, 100, 40, tail=(20, 70))
        cut = bubble - svg.Rect(0, 0, 100, 40)
        assert cut.bbox.y == pytest.approx(40)
        assert (bubble | svg.Circle(90, 10, 20)).bbox.width > 100


class TestCross:
    def test_twelve_sided_outline(self) -> None:
        sign = builder.cross(10, 20, 30, fill="green")
        assert sign.tag == "polygon" and len(sign.points) == 12
        assert (sign.bbox.x, sign.bbox.y, sign.bbox.width, sign.bbox.height) == pytest.approx((-5, 5, 30, 30))
        assert sign.get("fill") == "green"

    def test_thickness(self) -> None:
        thin = builder.cross(0, 0, 40, thickness=4)
        assert thin.bbox.width == 40
        assert (builder.cross(0, 0, 40, thickness=40).bbox.width) == 40
        assert (thin & svg.Rect(-20, -2, 40, 4)).bbox.width == pytest.approx(40)
        assert (thin - svg.Rect(-2, -20, 4, 40)).bbox.width == pytest.approx(40)

    @pytest.mark.parametrize("thickness", [0, -1, 50])
    def test_rejects_bad_thickness(self, thickness: float) -> None:
        with pytest.raises(ValueError):
            builder.cross(0, 0, 40, thickness=thickness)


class TestGrid:
    def test_cells(self) -> None:
        sheet = builder.grid(5, 5, 20, 10, rows=2, cols=4, stroke="gray")
        valid(sheet)
        text = str(sheet.d)
        assert text.count("M") == 3 + 5
        assert (sheet.bbox.x, sheet.bbox.y, sheet.bbox.width, sheet.bbox.height) == (5, 5, 20, 10)
        assert sheet.get("fill") == "none" and sheet.get("stroke") == "gray"

    def test_spacing(self) -> None:
        sheet = builder.grid(0, 0, 50, 30, spacing=10)
        assert str(sheet.d).count("M") == 4 + 6
        uneven = builder.grid(0, 0, 25, 25, spacing=(10, 5))
        assert str(uneven.d).count("M") == 6 + 3
        assert uneven.bbox.width == 25

    @pytest.mark.parametrize(
        "options",
        [{}, {"rows": 2}, {"rows": 2, "cols": 2, "spacing": 5}, {"spacing": 0}, {"rows": 0, "cols": 2}],
    )
    def test_rejects_bad_arguments(self, options: dict[str, object]) -> None:
        with pytest.raises(ValueError):
            builder.grid(0, 0, 10, 10, **options)  # type: ignore[arg-type]


class TestSpiral:
    def test_radius_grows_linearly(self) -> None:
        coil = builder.spiral(50, 50, turns=3, start_radius=2, end_radius=32, stroke="black")
        valid(coil)
        assert coil.get("fill") == "none"
        end = str(coil.d).split()[-2:]
        assert math.hypot(float(end[0]) - 50, float(end[1]) - 50) == pytest.approx(32, abs=1e-3)
        assert (coil.bbox.x, coil.bbox.x + coil.bbox.width) == pytest.approx((23, 82), abs=0.05)

    def test_every_segment_is_a_cubic(self) -> None:
        coil = builder.spiral(0, 0, turns=2.5, start_radius=0, end_radius=10)
        assert str(coil.d).count("C") == 10
        assert str(coil.d).count("L") == 0

    def test_curve_stays_on_the_archimedean_radius(self) -> None:
        coil = builder.spiral(0, 0, turns=2, start_radius=0, end_radius=20)
        pitch = 20 / (4 * math.pi)
        for index in range(1, 40):
            point = coil.point_at_length(coil.total_length() * index / 40)
            radius = math.hypot(point.x, point.y)
            direction = math.atan2(point.y, point.x)
            assert math.cos(direction - radius / pitch) == pytest.approx(1, abs=1e-4)

    def test_rejects_no_turns(self) -> None:
        with pytest.raises(ValueError):
            builder.spiral(0, 0, turns=0, start_radius=0, end_radius=5)


class TestWave:
    def test_sine_is_smooth_cubics_with_exact_amplitude(self) -> None:
        line = builder.wave(0, 10, 100, amplitude=8, wavelength=50, stroke="black")
        valid(line)
        assert line.get("fill") == "none"
        assert str(line.d).count("C") == 4
        assert (line.bbox.x, line.bbox.y, line.bbox.width, line.bbox.height) == pytest.approx((0, 2, 100, 16))

    def test_sine_matches_the_true_curve(self) -> None:
        line = builder.wave(0, 0, 40, amplitude=10, wavelength=40)
        for index in range(1, 40):
            point = line.point_at_length(line.total_length() * index / 40)
            assert point.y == pytest.approx(-10 * math.sin(2 * math.pi * point.x / 40), abs=0.2)

    def test_sine_is_cut_at_the_width(self) -> None:
        line = builder.wave(5, 0, 33, amplitude=4, wavelength=20)
        assert line.bbox.x == 5 and line.bbox.width == pytest.approx(33)
        assert str(line.d).count("C") == 4

    @pytest.mark.parametrize("kind", ["square", "triangle", "sawtooth"])
    def test_polylines_span_the_width(self, kind: str) -> None:
        line = builder.wave(0, 0, 70, amplitude=6, wavelength=20, kind=kind)
        valid(line)
        assert line.bbox.width == pytest.approx(70)
        assert line.bbox.height <= 12 + 1e-9
        assert "C" not in str(line.d)

    def test_square_wave_has_vertical_jumps(self) -> None:
        text = str(builder.wave(0, 0, 40, amplitude=5, wavelength=20, kind="square").d)
        assert text == "M0 -5 L10 -5 L10 5 L20 5 L20 -5 L30 -5 L30 5 L40 5"

    def test_triangle_and_sawtooth_shapes(self) -> None:
        assert str(builder.wave(0, 0, 20, amplitude=5, wavelength=20, kind="triangle").d) == "M0 0 L5 -5 L15 5 L20 0"
        assert str(builder.wave(0, 0, 40, amplitude=5, wavelength=20, kind="sawtooth").d) == "M0 5 L20 -5 L20 5 L40 -5"

    def test_rejects_bad_arguments(self) -> None:
        with pytest.raises(ValueError):
            builder.wave(0, 0, 10, amplitude=1, wavelength=5, kind="noise")
        with pytest.raises(ValueError):
            builder.wave(0, 0, 0, amplitude=1, wavelength=5)
        with pytest.raises(ValueError):
            builder.wave(0, 0, 10, amplitude=1, wavelength=0)


class TestRegistration:
    def test_new_presets_are_registered(self) -> None:
        names = set(svg.SHAPES.names())
        assert {"regular_polygon", "heart", "callout", "cross", "grid", "spiral", "wave"} <= names
        assert svg.SHAPES.get("heart") is builder.heart

    def test_every_preset_is_exported(self) -> None:
        for name in ("regular_polygon", "heart", "callout", "cross", "grid", "spiral", "wave"):
            assert name in builder.__all__

    def test_group_composition(self) -> None:
        doc = svg.Document(100, 100)
        doc += svg.Group(builder.heart(0, 0, 20), builder.cross(0, 0, 10)).place(50, 50).rotate(10)
        wellformed(str(doc))
