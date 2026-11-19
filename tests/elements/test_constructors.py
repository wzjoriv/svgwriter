from __future__ import annotations

import svgwriter as svg
from svgwriter.pathdata import BBox


def test_rect_from_corners_center_and_square() -> None:
    assert svg.Rect.from_corners((30, 40), (10, 20)).bbox == (10, 20, 20, 20)
    assert svg.Rect.from_center((50, 50), (20, 10)).bbox == (40, 45, 20, 10)
    assert svg.Rect.square(10, center=(0, 0)).bbox == (-5, -5, 10, 10) and svg.Rect.square(4).bbox == (0, 0, 4, 4)


def test_ellipse_and_circle_from_bbox() -> None:
    box = BBox(0, 0, 40, 20)
    assert svg.Ellipse.from_bbox(box).bbox == box
    assert svg.Circle.from_bbox(box).bbox == (10, 0, 20, 20)


def test_length_reads_are_floats_unless_they_have_units() -> None:
    c = svg.Circle(5, 6, 7)
    assert (c.cx, c.cy, c.r) == (5.0, 6.0, 7.0) and all(isinstance(v, float) for v in (c.cx, c.cy, c.r))
    parsed = svg.parse('<rect x="3" width="2mm" height="50%"/>')
    assert parsed.x == 3.0 and str(parsed.width) == "2mm" and str(parsed.height) == "50%"
    assert svg.Rect().rx is None


def test_lowercase_aliases_carry_constructors() -> None:
    assert svg.rect.from_center((0, 0), (2, 2)).bbox == (-1, -1, 2, 2)
