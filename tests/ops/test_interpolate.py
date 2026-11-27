import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal._flat._flatten import polylines
from svgwriter.catalog.paths import star


def test_numbers_points_colors_and_discrete_values():
    assert svg.interpolate(0, 10, 0.25) == 2.5
    assert svg.interpolate((0, 0), (10, 20), 0.5) == (5, 10)
    assert svg.interpolate("red", "blue", 0.5).hex == "#800080"


def test_values_that_do_not_blend_raise():
    with pytest.raises(TypeError, match="cannot interpolate int and str"):
        svg.interpolate(1, "bold", 0.5)
    with pytest.raises(TypeError):
        svg.interpolate("none", "red", 0.5)


def test_attributes_that_do_not_blend_switch_halfway():
    a, b = svg.rect(0, 0, 10, 10, fill="none"), svg.rect(0, 0, 10, 10, fill="red")
    assert svg.interpolate(a, b, 0.4).get("fill") == "none"
    assert str(svg.interpolate(a, b, 0.6).get("fill")) in ("red", "#ff0000")


def test_registered_rules_win_and_unregister():
    class Weight(int):
        pass

    svg.register_interpolator(Weight, lambda a, b, t: Weight(round(a + (b - a) * t, -2)))
    try:
        assert svg.interpolate(Weight(400), Weight(700), 0.5) == 600
    finally:
        svg.unregister_interpolator(Weight)
    assert svg.interpolate(Weight(400), Weight(700), 0.5) == 550
    with pytest.raises(KeyError):
        svg.unregister_interpolator(Weight)


def test_predicate_rules():
    def is_word(value):
        return isinstance(value, str) and value.isalpha()

    svg.register_interpolator(is_word, lambda a, b, t: a if t < 0.5 else b)
    try:
        assert svg.interpolate("thin", "bold", 0.7) == "bold"
    finally:
        svg.unregister_interpolator(is_word)


def test_matrix_turns_the_short_way():
    a, b = svg.Matrix.rotate(350), svg.Matrix.rotate(10)
    assert svg.interpolate(a, b, 0.5).decompose()[2] == pytest.approx(0, abs=1e-9)


def test_same_shape_elements_blend_attributes_and_transform():
    a = svg.rect(0, 0, 10, 10, fill="red")
    b = svg.rect(10, 0, 20, 10, fill="blue").rotate(90)
    mid = svg.interpolate(a, b, 0.5)
    assert mid.tag == "rect" and (mid.x, mid.width) == (5, 15) and mid.fill.hex == "#800080"
    assert str(svg.interpolate(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10).rotate(90), 0.5).matrix) == "rotate(45 5 5)"
    assert a.x == 0 and b.x == 10


def test_polygons_with_equal_point_counts_blend_points():
    mid = svg.interpolate(svg.Polygon([(0, 0), (1, 0), (0, 1)]), svg.Polygon([(0, 0), (3, 0), (0, 3)]), 0.5)
    assert mid.tag == "polygon" and np.asarray(mid.points).tolist() == [[0, 0], [2, 0], [0, 2]]


@pytest.mark.parametrize("t", [0.0, 1.0])
def test_morph_endpoints_match_the_shapes(t):
    a, b = star(50, 50, 40), svg.circle(50, 50, 30)
    morph = svg.interpolate(a, b, t)
    expected = (a if t == 0 else b).bounds()
    assert morph.tag == "path"
    assert morph.bounds() == pytest.approx(expected, abs=0.05)


def test_morph_handles_different_subpath_counts():
    ring = svg.circle(0, 0, 10) - svg.circle(0, 0, 5)
    mid = svg.interpolate(svg.rect(-10, -10, 20, 20), ring, 0.5)
    assert len(mid.d.subpaths()) == 2


def test_item_assignment_replaces_in_place():
    doc = svg.Document(10, 10)
    doc.rect(0, 0, 1, 1, id="a")
    doc.rect(2, 2, 1, 1)
    doc[0] = svg.circle(1, 1, 1)
    assert [e.tag for e in doc] == ["circle", "rect"] and doc[0].id == "a"
    group = svg.group(svg.rect(0, 0, 1, 1), svg.rect(0, 0, 1, 1))
    group[1] = svg.circle(0, 0, 1)
    assert [e.tag for e in group] == ["rect", "circle"]


def _filled_area(path):
    total = 0.0
    for points, _ in polylines(path.d, 0.05):
        xy = np.asarray(points)
        total += float(np.dot(xy[:, 0], np.roll(xy[:, 1], -1)) - np.dot(np.roll(xy[:, 0], -1), xy[:, 1])) / 2
    return abs(total)


RING = svg.circle(0, 0, 40) - svg.circle(0, 0, 20)


@pytest.mark.parametrize("a, b", [
    (RING, star(0, 0, 45, points=5)),
    (svg.rect(-35, -35, 70, 70), svg.circle(0, 0, 40)),
    (svg.circle(0, 0, 40), svg.Polygon([(0, -45), (40, 30), (-40, 30)])),
    (svg.text_to_path("A", size=100), svg.text_to_path("B", size=100)),
])
def test_morph_does_not_twist(a, b):
    ends = [_filled_area(svg.interpolate(a, b, t)) for t in (0, 1)]
    middle = _filled_area(svg.interpolate(a, b, 0.5))
    assert 0.7 * min(ends) < middle < 1.3 * max(ends)


def test_morph_pairs_outlines_with_outlines_and_holes_with_holes():
    letter = svg.text_to_path("B", size=100)
    assert len(letter.d.subpaths()) == 3
    for t in (0, 0.5, 1):
        assert len(svg.interpolate(letter, RING, t).d.subpaths()) == 3
    gone = svg.interpolate(RING, svg.circle(0, 0, 40), 1)
    hole = gone.d.subpaths()[1].bbox
    assert hole.width == pytest.approx(0, abs=1e-9) and hole.height == pytest.approx(0, abs=1e-9)


def test_morph_is_deterministic_and_symmetric_at_the_ends():
    a, b = svg.text_to_path("A", size=100), RING
    assert str(svg.interpolate(a, b, 0.3).d) == str(svg.interpolate(a.clone(), b.clone(), 0.3).d)
    assert svg.interpolate(a, b, 0).bounds() == pytest.approx(a.bounds(), abs=0.05)
