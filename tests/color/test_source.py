from __future__ import annotations

import pytest

import svgwriter as svg

P3_GREEN = "color(display-p3 0 1 0)"


@pytest.mark.parametrize(("text", "space"), [
    ("oklch(0.7 0.3 145)", "oklch"),
    ("oklab(0.7 -0.2 0.1)", "oklab"),
    ("lab(50 60 -30)", "lab"),
    ("lch(50 60 300)", "lch"),
    (P3_GREEN, "display-p3"),
    ("color(rec2020 0 1 0)", "rec2020"),
    ("color(xyz 0.2 0.3 0.4)", "xyz-d65"),
])
def test_css_functions_keep_their_space_and_exact_channels(text, space):
    color = svg.Color.parse(text)
    assert color.space == space
    assert color.source is not None and color.source[0] == space


@pytest.mark.parametrize("text", ["red", "#ff8000", "rgb(10 20 30)", "hsl(120 50% 50%)", "color(srgb 0.2 0.4 0.6)",
                                  "device-cmyk(0 1 1 0)"])
def test_srgb_inputs_carry_no_source(text):
    assert svg.Color.parse(text).source is None
    assert svg.Color.parse(text).space == "srgb"


def test_hex_and_svg_output_stay_clipped_srgb():
    green = svg.Color.parse(P3_GREEN)
    assert green.hex == "#00ff00"
    assert str(svg.rect(0, 0, 1, 1, fill=green)) == str(svg.rect(0, 0, 1, 1, fill="#00ff00"))
    assert not green.in_gamut and svg.Color.parse("lime").in_gamut


def test_mixing_wide_colors_does_not_clip_first():
    green = svg.Color.parse(P3_GREEN)
    mixed = green.mix(P3_GREEN, 0.5, space="display-p3")
    assert mixed.coords("display-p3") == pytest.approx((0, 1, 0))
    half = green.mix("white", 0.5, space="display-p3")
    assert half.coords("display-p3") == pytest.approx((0.5, 1, 0.5))
    assert half.hex != svg.Color.parse("lime").mix("white", 0.5, space="display-p3").hex


def test_mixing_srgb_colors_gives_plain_srgb_colors():
    for space in ("srgb", "linear", "oklab", "oklch", "lab", "lch", "display-p3", "xyz"):
        assert svg.Color.parse("red").mix("blue", 0.3, space=space).source is None


@pytest.mark.parametrize(("space", "expected"), [
    ("srgb", "#ff0000"),
    ("hsl", "hsl(0 100% 50%)"),
    ("hwb", "hwb(0 0% 0%)"),
    ("lab", "lab(54.29 80.8 69.89)"),
    ("oklch", "oklch(0.63 0.26 29.23)"),
    ("display-p3", "color(display-p3 0.92 0.2 0.14)"),
    ("xyz-d65", "color(xyz-d65 0.41 0.21 0.02)"),
])
def test_to_css_writes_each_space(space, expected):
    assert svg.Color(1, 0, 0).to_css(space, precision=2) == expected


def test_to_css_round_trips_wide_gamut_colors():
    for space in ("display-p3", "rec2020", "oklch", "lab"):
        green = svg.Color.parse(P3_GREEN)
        back = svg.Color.parse(green.to_css(space, precision=8))
        assert back.coords("display-p3") == pytest.approx((0, 1, 0), abs=1e-5)


def test_to_css_writes_alpha_after_a_slash():
    assert svg.Color(0, 0, 1, 0.25).to_css("oklab", precision=2) == "oklab(0.45 -0.03 -0.31 / 0.25)"


def test_from_space_keeps_in_gamut_srgb_plain():
    assert svg.Color.from_space("srgb", (0.2, 0.4, 0.6)) == svg.Color(0.2, 0.4, 0.6)
    assert svg.Color.from_space("srgb", (1.2, 0.4, 0.6)).source == ("srgb", (1.2, 0.4, 0.6))
    with pytest.raises(ValueError, match="unknown colour space"):
        svg.Color.from_space("cmyk", (0, 0, 0))


def test_with_alpha_and_icc_keep_the_source():
    green = svg.Color.parse(P3_GREEN)
    assert green.with_alpha(0.5).source == green.source
    assert svg.Color.parse(P3_GREEN + " icc-color(p, 1)").source == green.source
