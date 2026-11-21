from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.color._difference import ciede2000

SHARMA_2005 = [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
    ((50.0, 2.8361, -74.0200), (50.0, 0.0, -82.7485), 3.4412),
    ((50.0, -1.3802, -84.2814), (50.0, 0.0, -82.7485), 1.0000),
    ((50.0, -1.1848, -84.8006), (50.0, 0.0, -82.7485), 1.0000),
    ((50.0, -0.9009, -85.5211), (50.0, 0.0, -82.7485), 1.0000),
    ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
    ((50.0, -1.0, 2.0), (50.0, 0.0, 0.0), 2.3669),
    ((50.0, 2.4900, -0.0010), (50.0, -2.4900, 0.0009), 7.1792),
    ((50.0, 2.4900, -0.0010), (50.0, -2.4900, 0.0010), 7.1792),
    ((50.0, 2.4900, -0.0010), (50.0, -2.4900, 0.0011), 7.2195),
    ((50.0, 2.4900, -0.0010), (50.0, -2.4900, 0.0012), 7.2195),
    ((50.0, -0.0010, 2.4900), (50.0, 0.0009, -2.4900), 4.8045),
    ((50.0, -0.0010, 2.4900), (50.0, 0.0010, -2.4900), 4.8045),
    ((50.0, -0.0010, 2.4900), (50.0, 0.0011, -2.4900), 4.7461),
    ((50.0, 2.5, 0.0), (50.0, 0.0, -2.5), 4.3065),
    ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
    ((50.0, 2.5, 0.0), (61.0, -5.0, 29.0), 22.8977),
    ((50.0, 2.5, 0.0), (56.0, -27.0, -3.0), 31.9030),
    ((50.0, 2.5, 0.0), (58.0, 24.0, 15.0), 19.4535),
    ((50.0, 2.5, 0.0), (50.0, 3.1736, 0.5854), 1.0000),
    ((50.0, 2.5, 0.0), (50.0, 3.2972, 0.0), 1.0000),
    ((50.0, 2.5, 0.0), (50.0, 1.8634, 0.5757), 1.0000),
    ((50.0, 2.5, 0.0), (50.0, 3.2592, 0.3350), 1.0000),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ((63.0109, -31.0961, -5.8663), (62.8187, -29.7946, -4.0864), 1.2630),
    ((61.2901, 3.7196, -5.3901), (61.4292, 2.2480, -4.9620), 1.8731),
    ((35.0831, -44.1164, 3.7933), (35.0232, -40.0716, 1.5901), 1.8645),
    ((22.7233, 20.0904, -46.6940), (23.0331, 14.9730, -42.5619), 2.0373),
    ((36.4612, 47.8580, 18.3852), (36.2715, 50.5065, 21.2231), 1.4146),
    ((90.8027, -2.0831, 1.4410), (91.1528, -1.6435, 0.0447), 1.4441),
    ((90.9257, -0.5406, -0.9208), (88.6381, -0.8985, -0.7239), 1.5381),
    ((6.7747, -0.2908, -2.4247), (5.8714, -0.0985, -2.2286), 0.6377),
    ((2.0776, 0.0795, -1.1350), (0.9033, -0.0636, -0.5514), 0.9082),
]
"""The 34 reference pairs of Sharma, Wu and Dalal (2005), Table 1."""


@pytest.mark.parametrize(("first", "second", "expected"), SHARMA_2005)
def test_ciede2000_matches_the_sharma_reference_pairs(first, second, expected):
    assert ciede2000(first, second) == pytest.approx(expected, abs=1e-4)
    assert ciede2000(second, first) == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize(("first", "second", "expected"), SHARMA_2005)
def test_delta_e2000_compares_lab_colors_exactly(first, second, expected):
    a, b = svg.Color.from_space("lab", first), svg.Color.from_space("lab", second)
    assert a.delta_e2000(b) == pytest.approx(expected, abs=1e-4)


def test_identical_colors_have_no_difference():
    assert svg.Color.parse("teal").delta_e2000("teal") == 0
    assert svg.Color.parse("teal").delta("#008080") == 0


def test_delta_is_the_oklab_distance_and_ignores_alpha():
    red, blue = svg.Color.parse("red"), svg.Color.parse("blue")
    expected = sum((a - b) ** 2 for a, b in zip(red.coords("oklab"), blue.coords("oklab"), strict=False)) ** 0.5
    assert red.delta(blue.with_alpha(0.2)) == pytest.approx(expected)
    assert svg.Color.parse("black").delta("white") == pytest.approx(1.0, abs=1e-6)


def test_delta_sees_wide_gamut_differences_that_clipping_hides():
    green = svg.Color.parse("color(display-p3 0 1 0)")
    assert green.hex == "#00ff00"
    assert green.delta("lime") > 0.05
