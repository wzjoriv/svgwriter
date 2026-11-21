from __future__ import annotations

import pytest

import svgwriter as svg

RED = "#ff0000"


@pytest.mark.parametrize(("text", "expected"), [
    ("oklch(62.8% 0.2577 29.23)", RED),
    ("oklch(0.628 0.2577 29.23deg)", RED),
    ("oklab(0.628 0.2249 0.1258)", RED),
    ("lab(54.29 80.8 69.89)", RED),
    ("lch(54.29 106.84 40.85)", RED),
    ("color(srgb 1 0 0)", RED),
    ("color(display-p3 0.9175 0.2003 0.1386)", RED),
    ("color(a98-rgb 0.8584 0 0)", RED),
    ("color(rec2020 0.7919 0.2309 0.0739)", RED),
    ("color(xyz-d65 0.4124 0.2126 0.0193)", RED),
    ("color(xyz-d50 0.4361 0.2225 0.0139)", RED),
    ("color(srgb-linear 0.2158 0.2158 0.2158)", "#808080"),
    ("hwb(120 20% 30%)", "#33b233"),
    ("hwb(0 60% 60%)", "#808080"),
    ("hsv(240 100% 100%)", "#0000ff"),
    ("hsva(0, 0%, 100%, 0.5)", "#ffffff80"),
    ("device-cmyk(0 1 1 0)", RED),
    ("device-cmyk(0% 0% 0% 100%)", "#000000"),
    ("rgb(255 0 0 / 50%)", "#ff000080"),
    ("rgb(none 128 255)", "#0080ff"),
    ("rgb(100% 0 0)", RED),
    ("rgb(1 0 0)", "#010000"),
    ("hsl(120 100 50)", "#00ff00"),
    ("hsl(0.5turn 100% 50%)", "#00ffff"),
])
def test_css_color_4_reference_values(text: str, expected: str) -> None:
    assert svg.Color.parse(text).hex == expected


def test_out_of_gamut_colors_are_clipped() -> None:
    assert svg.Color.parse("color(display-p3 0 1 0)").hex == "#00ff00"
    assert all(0.0 <= c <= 1.0 for c in svg.Color.parse("lab(100 -200 200)").rgb)


@pytest.mark.parametrize("text", ["color(prophoto-rgb 1 0 0)", "oklch(1 2)", "lab(1 2 3 4 5)", "rgb(a b c)",
                                  "rgb(1 2 3 /)"])
def test_bad_functions_are_rejected(text: str) -> None:
    with pytest.raises(ValueError):
        svg.Color.parse(text)


class TestMix:
    def test_spaces(self) -> None:
        red = svg.Color.parse("red")
        assert red.mix("blue").hex == "#800080"
        assert red.mix("blue", space="linear").hex == "#bc00bc"
        assert red.mix("blue", space="oklab").hex == "#8c53a2"
        assert red.mix("blue", space="oklch").hex == "#ba00c2"
        assert red.mix("blue", 0, space="oklch").hex == RED

    def test_unknown_space(self) -> None:
        with pytest.raises(ValueError, match="mixing space"):
            svg.Color.parse("red").mix("blue", space="hsl")  # type: ignore[arg-type]


class TestAdjust:
    def test_hue_and_saturation(self) -> None:
        red = svg.Color.parse("red")
        assert red.hue_shift(240).hex == "#0000ff" and red.complement().hex == "#00ffff"
        assert red.desaturate(1).hex == "#808080" and red.desaturate(1).saturate(1).hex == RED

    def test_grey_and_invert(self) -> None:
        grey = svg.Color.parse("#3366cc").grayscale()
        assert grey.uint8[0] == grey.uint8[1] == grey.uint8[2]
        assert svg.Color.parse("white").invert().hex == "#000000"

    def test_contrast_and_readable(self) -> None:
        navy, yellow = svg.Color.parse("navy"), svg.Color.parse("yellow")
        assert navy.contrast(yellow) == pytest.approx(yellow.contrast(navy))
        assert svg.Color.parse("white").contrast("white") == pytest.approx(1.0)
        assert navy.is_dark and yellow.is_light
        assert navy.readable().hex == "#ffffff" and yellow.readable().hex == "#000000"
        assert navy.readable("#111111", "#eeeeee").hex == "#eeeeee"
