import numpy as np
import pytest

import svgwriter as svg
from svgwriter.builder import star


def test_numbers_points_colors_and_discrete_values():
    assert svg.interpolate(0, 10, 0.25) == 2.5
    assert svg.interpolate((0, 0), (10, 20), 0.5) == (5, 10)
    assert svg.interpolate("red", "blue", 0.5).hex == "#800080"
    assert svg.interpolate("none", "red", 0.4) == "none" and svg.interpolate("none", "red", 0.6) == "red"


def test_matrix_turns_the_short_way():
    a, b = svg.Matrix.rotate(350), svg.Matrix.rotate(10)
    assert svg.interpolate(a, b, 0.5).decompose()[2] == pytest.approx(0, abs=1e-9)


def test_same_shape_elements_blend_attributes_and_transform():
    a = svg.rect(0, 0, 10, 10, fill="red")
    b = svg.rect(10, 0, 20, 10, fill="blue").rotate(90)
    mid = svg.interpolate(a, b, 0.5)
    assert mid.tag == "rect" and (mid.x, mid.width) == (5, 15) and mid.fill.hex == "#800080"
    assert str(svg.interpolate(svg.rect(0, 0, 10, 10), svg.rect(0, 0, 10, 10).rotate(90), 0.5).t) == "rotate(45 5 5)"
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
    group = svg.group(svg.rect(), svg.rect())
    group[1] = svg.circle()
    assert [e.tag for e in group] == ["rect", "circle"]
