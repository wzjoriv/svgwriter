from __future__ import annotations

import pytest

import svgwriter as svg

TEAL = svg.Color.parse("#0f766e")


@pytest.mark.parametrize("method", ["tint", "shade"])
def test_tint_and_shade_keep_the_oklab_hue(method):
    _, _, hue = TEAL.coords("oklch")
    for amount in (0.2, 0.5, 0.8):
        result = svg.Color.from_space("oklab", getattr(TEAL, method)(amount).coords("oklab"))
        assert result.coords("oklch")[2] == pytest.approx(hue, abs=1.5)


def test_tint_and_shade_reach_white_and_black_and_keep_alpha():
    assert TEAL.tint(1).hex == "#ffffff"
    assert TEAL.shade(1).hex == "#000000"
    assert TEAL.tint(0).hex == TEAL.hex
    assert TEAL.with_alpha(0.5).tint(0.3).a == 0.5


def test_tint_steps_are_even_in_oklab_lightness():
    lightness = [TEAL.tint(step / 4).coords("oklab")[0] for step in range(5)]
    gaps = [b - a for a, b in zip(lightness, lightness[1:], strict=False)]
    assert gaps == pytest.approx([gaps[0]] * 4, rel=0.05)


def test_tint_of_a_wide_gamut_color_stays_wide():
    green = svg.Color.parse("color(display-p3 0 1 0)")
    assert not green.tint(0.1).in_gamut
    assert green.tint(0.1).space == "oklab"


@pytest.mark.parametrize(("steps", "expected"), [(2, "#00ffff"), (3, "#8080ff"), (5, "#4080bf")])
def test_posterize_rounds_each_channel_to_even_levels(steps, expected):
    assert svg.Color.parse("#5a9ad0").posterize(steps).hex == expected


def test_posterize_needs_two_steps():
    with pytest.raises(ValueError, match="at least 2"):
        TEAL.posterize(1)


def test_sepia_follows_the_css_filter_matrix():
    r, g, b = 0.2, 0.4, 0.8
    toned = svg.Color(r, g, b).sepia()
    assert toned.rgb == pytest.approx((0.393 * r + 0.769 * g + 0.189 * b, 0.349 * r + 0.686 * g + 0.168 * b,
                                       0.272 * r + 0.534 * g + 0.131 * b))
    assert svg.Color(r, g, b).sepia(0).rgb == pytest.approx((r, g, b))
    assert svg.Color(1, 1, 1).sepia().hex == "#ffffef"


def test_gamma_raises_channels_to_a_power():
    assert svg.Color(0.5, 0.25, 1, 0.3).gamma(2).rgba == pytest.approx((0.25, 0.0625, 1, 0.3))
    with pytest.raises(ValueError, match="above 0"):
        TEAL.gamma(0)
