"""Path tools on laid-out elements: distributing along a placed path and rounding a stretched background."""

import pytest

import svgwriter as svg

RAIL_LENGTH = 60
OFFSET = 20
RADIUS = 3


def test_distribute_follows_a_path_placed_by_a_stack():
    rail = svg.path(f"M0 0 H{RAIL_LENGTH}")
    doc = svg.Document(100, 100)
    doc += svg.VStack(svg.rect(0, 0, RAIL_LENGTH, 10), rail, gap=OFFSET - 10)
    dots = svg.distribute([doc.circle(0, 0, 2) for _ in range(3)], along=rail)
    centres = [(dot.bounds().x + 2, dot.bounds().y + 2) for dot in dots]
    assert centres == [pytest.approx((x, OFFSET)) for x in (0, RAIL_LENGTH / 2, RAIL_LENGTH)]


def test_distributed_group_is_laid_out_by_its_bounds():
    dots = [svg.circle(0, 0, 2) for _ in range(5)]
    svg.distribute(dots, along=svg.path("M0 0 C 20 -20 40 20 60 0"))
    row = svg.group(*dots)
    label = svg.text("Dots", font_size=10)
    stack = svg.VStack(label, row, gap=4)
    assert row.bounds().y >= label.bounds().y + label.bounds().height + 4
    assert stack.bounds().width == pytest.approx(row.bounds().width)


@pytest.mark.parametrize("background", ["surface", svg.rect(0, 0, 1, 1).as_role("surface")])
def test_round_corners_on_a_stretched_background(background):
    stack = svg.VStack(svg.rect(0, 0, 30, 10), padding=4, background=background)
    doc = svg.Document(100, 100)
    doc += stack
    rounded = stack.background.round_corners(RADIUS)
    assert rounded.bounds() == stack.bounds()
    stack.background = rounded
    text = doc.to_string()
    assert 'd=""' not in text and "role-surface" in text
    assert stack.background.bounds() == svg.BBox(0, 0, 38, 18)
