from __future__ import annotations

import pytest

import svgwriter as svg
from svgwriter.model.attributes import FuncIRI
from svgwriter.model.color import (
    NAMED_COLORS,
    Color,
    PaintKeyword,
    PaintRef,
    as_color,
    clamp,
    parse_color,
    parse_paint,
)


def test_named_color_count() -> None:
    assert len(NAMED_COLORS) == 147
    assert NAMED_COLORS["purple"] == (128, 0, 128)


@pytest.mark.parametrize(
    ("text", "rgba"),
    [
        ("red", (255, 0, 0, 255)),
        ("ReD", (255, 0, 0, 255)),
        ("#f80", (255, 136, 0, 255)),
        ("#FF8800", (255, 136, 0, 255)),
        ("#ff880080", (255, 136, 0, 128)),
        ("#f808", (255, 136, 0, 136)),
        ("rgb(1, 2, 3)", (1, 2, 3, 255)),
        ("rgb(100%, 50%, 0%)", (255, 128, 0, 255)),
        ("rgb(300, -5, 0)", (255, 0, 0, 255)),
        ("rgba(0, 0, 255, 0.5)", (0, 0, 255, 128)),
        ("rgb(0 0 255 / 50%)", (0, 0, 255, 128)),
        ("hsl(120, 100%, 50%)", (0, 255, 0, 255)),
        ("hsla(240deg, 100%, 50%, 0.25)", (0, 0, 255, 64)),
    ],
)
def test_parse(text: str, rgba: tuple[int, int, int, int]) -> None:
    assert parse_color(text).uint8 == rgba


@pytest.mark.parametrize("bad", ["#12", "#1234567", "#ggg", "rgb(1,2)", "rgb(1%,2,3)", "notacolor"])
def test_parse_rejects(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_color(bad)


def test_floats_are_the_model() -> None:
    c = Color(1, 0.5, 0)
    assert c.rgba == (1, 0.5, 0, 1.0) and list(c) == [1, 0.5, 0, 1.0] and c.hex == "#ff8000"
    assert Color.from_uint8(255, 128, 0) == Color(1, 128 / 255, 0)


def test_channel_validation_points_to_uint8() -> None:
    with pytest.raises(ValueError, match="from_uint8"):
        Color(255, 0, 0)
    with pytest.raises(ValueError, match="g=-0.5"):
        Color(0, -0.5, 0)


@pytest.mark.parametrize(
    ("value", "hex_"),
    [("navy", "#000080"), ((0, 0, 1), "#0000ff"), ([0, 1, 0, 0.5], "#00ff0080"), (Color(1, 1, 1), "#ffffff")],
)
def test_as_color(value: object, hex_: str) -> None:
    assert as_color(value).hex == hex_  # type: ignore[arg-type]


def test_as_color_rejects() -> None:
    with pytest.raises(TypeError):
        as_color(5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="3 or 4"):
        as_color((1, 0))
    with pytest.raises(ValueError, match="from_uint8"):
        as_color((255, 0, 0))


def test_names_and_output() -> None:
    assert str(parse_color("tomato")) == "tomato"
    assert str(Color.from_uint8(255, 99, 71)) == "#ff6347"
    assert parse_color("tomato") == Color.from_uint8(255, 99, 71)
    assert str(parse_color("tomato").with_alpha(0.5)) == "#ff6347"
    assert parse_color("red").with_alpha(0.5).to_css() == "rgba(255, 0, 0, 0.5)"
    assert parse_color("red").to_css() == "red"


def test_icc_color() -> None:
    color = parse_color("#cd853f icc-color(acmecmyk, 0.11, 0.48, 0.83, 0.00)")
    assert color.uint8[:3] == (205, 133, 63)
    assert str(color) == "#cd853f icc-color(acmecmyk, 0.11, 0.48, 0.83, 0.00)"
    assert Color(0, 0, 0).with_icc("icc-color(x, 1)").icc == "icc-color(x, 1)"


def test_hsl_round_trip() -> None:
    assert Color(1, 0, 0).hsl == pytest.approx((0.0, 1.0, 0.5))
    assert Color.from_hsl(120, 1, 0.5).hex == "#00ff00"


def test_lighten_darken_mix() -> None:
    red = Color(1, 0, 0)
    assert red.lighten(0.5).hex == "#ffffff" and red.darken(0.5).hex == "#000000"
    assert red.mix("blue").hex == "#800080" and red.mix((0, 0, 1), 0).hex == "#ff0000"
    assert red.mix(Color(0, 0, 1, 0)).a == 0.5
    assert red.with_alpha(0.2).lighten(0.1).a == 0.2


def test_luminance() -> None:
    assert Color(1, 1, 1).luminance == pytest.approx(1.0)
    assert Color(0, 0, 0).luminance == 0.0


def test_clamp() -> None:
    assert clamp(5, 0, 3) == 3
    assert clamp(-1.5, 0.0, 1.0) == 0.0


def test_parse_paint() -> None:
    assert parse_paint("none") is PaintKeyword.NONE
    assert parse_paint("currentColor") is PaintKeyword.CURRENT_COLOR
    assert parse_paint("blue") == Color(0, 0, 1)
    ref = parse_paint("url(#grad) red")
    assert ref == PaintRef(FuncIRI("#grad"), Color(1, 0, 0))
    assert str(ref) == "url(#grad) red"
    assert str(parse_paint("url(#g) none")) == "url(#g) none"
    with pytest.raises(ValueError):
        parse_paint("url(#a) url(#b)")


class TestOnElements:
    def test_tuple_fill(self) -> None:
        r = svg.Rect(0, 0, 1, 1, fill=(1, 0, 0))
        assert 'fill="#ff0000"' in str(r) and not r.has("fill-opacity")

    def test_alpha_goes_to_matching_opacity(self) -> None:
        r = svg.Rect(0, 0, 1, 1, fill=(1, 0, 0, 0.5), stroke="rgba(0, 0, 255, 0.25)")
        assert r.get("fill-opacity") == 0.5 and str(r.get("fill")) == "#ff0000"
        assert r.get("stroke") == "rgba(0, 0, 255, 0.25)"
        r.stroke = Color.parse("rgba(0, 0, 255, 0.25)")
        assert r.get("stroke-opacity") == 0.25 and str(r.get("stroke")) == "#0000ff"
        assert svg.Stop(0, (0, 1, 0, 0.5)).get("stop-opacity") == 0.5
        assert svg.FeFlood(flood_color=(0, 0, 0, 0.3)).get("flood-opacity") == 0.3

    def test_attribute_without_opacity_rejects_alpha(self) -> None:
        with pytest.raises(ValueError, match="no opacity"):
            svg.FeDiffuseLighting(lighting_color=(1, 1, 1, 0.5))

    def test_paint_objects_pass_through(self) -> None:
        r = svg.Rect(0, 0, 1, 1, fill=PaintKeyword.NONE)
        r.stroke = PaintRef(FuncIRI("#g"))
        assert str(r.get("stroke")) == "url(#g)"
