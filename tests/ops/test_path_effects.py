import pytest

import svgwriter as svg


def test_roughen_is_repeatable_per_seed_and_keeps_paint():
    card = svg.rect(0, 0, 60, 30, fill="gold", stroke="black")
    one, two, other = card.roughen(seed=4), card.roughen(seed=4), card.roughen(seed=5)
    assert str(one.get("d")) == str(two.get("d")) != str(other.get("d"))
    assert one.get("fill") == "gold" and one.tag == "path"
    with pytest.raises(ValueError, match="segment must be positive"):
        card.roughen(0)


def test_dashed_cuts_the_outline_into_open_pieces():
    pieces = svg.line(0, 0, 30, 0, stroke="black").dashed(10, 5)
    moves = sum(type(command).__name__ == "MoveTo" for command in pieces.get("d"))
    assert moves == 2
    with pytest.raises(ValueError, match="positive length"):
        svg.line(0, 0, 30, 0).dashed(0)


def test_stamp_repeats_the_shape_and_checks_its_options():
    ticks = svg.line(0, 0, 100, 0, fill="black").stamp(svg.rect(-1, -3, 2, 6), 10)
    assert sum(type(command).__name__ == "MoveTo" for command in ticks.get("d")) == 10
    box = ticks.bounds()
    assert box.width == pytest.approx(92, abs=1) and box.height == pytest.approx(6, abs=0.1)
    with pytest.raises(ValueError, match="orient"):
        svg.line(0, 0, 10, 0).stamp(svg.circle(0, 0, 1), 2, orient="spin")


def test_taper_fills_with_the_stroke_and_follows_its_widths():
    brush = svg.line(0, 0, 100, 0, stroke="navy").taper(0, 10, 0)
    assert str(brush.get("fill")) == "navy" and str(brush.get("stroke")) == "none"
    assert brush.bounds().height == pytest.approx(10, abs=0.5)
    point = svg.line(0, 0, 100, 0, stroke="red").path_effect("taper", widths=lambda t: 8 * (1 - t))
    assert point.bounds().height == pytest.approx(8, abs=0.5)


def test_users_register_their_own_path_effects():
    @svg.preset.path_effect(fills=True)
    def thicken(data, *, width: float = 4) -> svg.PathData:
        return svg.path(data).stroked(width=width).get("d")

    try:
        assert "thicken" in svg.preset.path_effect.list()
        made = svg.line(0, 0, 50, 0, stroke="teal").path_effect("thicken", width=6)
        assert str(made.get("fill")) == "teal" and made.bounds().height == pytest.approx(6, abs=0.5)
    finally:
        svg.preset.path_effect.unregister("thicken")


def test_built_ins_are_listed_and_unknown_names_suggest():
    assert {"roughen", "dashed", "stamp", "taper"} <= set(svg.preset.path_effect.list())
    with pytest.raises(Exception, match="taper"):
        svg.line(0, 0, 1, 0).path_effect("tapr")
