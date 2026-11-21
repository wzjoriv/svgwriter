from __future__ import annotations

import pytest

from svgwriter.model.color._spaces import SPACES, convert, lab_to_srgb, oklab_to_srgb, srgb_to_oklab

SAMPLE = (0.3, 0.6, 0.9)


@pytest.mark.parametrize("space", sorted(SPACES))
def test_every_space_round_trips_through_srgb(space):
    there = convert(SAMPLE, "srgb", space)
    assert convert(there, space, "srgb") == pytest.approx(SAMPLE, abs=1e-6)


@pytest.mark.parametrize(("space", "expected"), [
    ("display-p3", (0.9175, 0.2003, 0.1386)),
    ("a98-rgb", (0.8584, 0.0, 0.0)),
    ("rec2020", (0.7919, 0.2309, 0.0739)),
    ("xyz-d65", (0.4124, 0.2126, 0.0193)),
    ("xyz-d50", (0.4361, 0.2225, 0.0139)),
    ("lab", (54.29, 80.8, 69.89)),
    ("lch", (54.29, 106.84, 40.85)),
    ("oklab", (0.628, 0.2249, 0.1258)),
    ("oklch", (0.628, 0.2577, 29.23)),
])
def test_srgb_red_matches_the_css_color_4_reference_values(space, expected):
    assert convert((1.0, 0.0, 0.0), "srgb", space) == pytest.approx(expected, abs=0.01)


def test_conversions_keep_values_outside_the_srgb_gamut():
    r, g, b = convert((0.0, 1.0, 0.0), "display-p3", "srgb")
    assert g > 1 and r < 0 and b < 0
    assert convert((r, g, b), "srgb", "display-p3") == pytest.approx((0.0, 1.0, 0.0), abs=1e-9)


def test_the_tree_route_matches_the_direct_conversions_exactly():
    assert convert(SAMPLE, "srgb", "oklab") == srgb_to_oklab(SAMPLE)
    assert convert((0.6, 0.1, 0.05), "oklab", "srgb") == oklab_to_srgb((0.6, 0.1, 0.05))
    assert convert((54.29, 80.8, 69.89), "lab", "srgb") == lab_to_srgb((54.29, 80.8, 69.89))


def test_an_unknown_space_is_named_in_the_error():
    with pytest.raises(ValueError, match="unknown colour space 'cmyk'"):
        convert(SAMPLE, "srgb", "cmyk")
