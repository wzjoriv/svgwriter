import pytest

import svgwriter as svg


@pytest.fixture
def scene():
    doc = svg.Document(width=200, height=100)
    return doc, doc.rect(20, 20, 100, 50)


def test_points_read_the_bounds(scene):
    _, box = scene
    assert box.center == (70, 45) and box.top_left == (20, 20) and box.bottom_right == (120, 70)
    assert (box.left, box.top, box.right, box.bottom) == (20, 20, 120, 70)
    assert box.top_center == (70, 20) and box.center_right == (120, 45)


def test_assigning_a_point_moves_the_element(scene):
    doc, box = scene
    dot = doc.circle(0, 0, 5)
    dot.center = box.center
    assert dot.center == box.center
    dot.top_left = box.bottom_right
    assert dot.top_left == (120, 70)


def test_assigning_an_edge_moves_one_axis(scene):
    doc, box = scene
    label = doc.rect(0, 0, 10, 4)
    label.top = box.top + 5
    assert label.top == 25 and label.left == 0
    label.right = box.right
    assert label.right == 120 and label.top == 25


def test_edges_take_lengths_in_page_units():
    doc = svg.Document(size="a4")
    tile = doc.rect(0, 0, 10, 10)
    tile.left = 2 * svg.cm
    assert tile.left == pytest.approx(20)


def test_rotated_elements_use_their_transformed_bounds(scene):
    doc, box = scene
    bar = doc.rect(0, 0, 40, 10).rotate(90)
    bar.center = box.center
    assert bar.center == pytest.approx(box.center)
    assert bar.bounds().width == pytest.approx(10)
