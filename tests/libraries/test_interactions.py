import re

import pytest

import svgwriter as svg


def test_builtins_are_registered_and_listed():
    assert {"button", "highlight"} <= set(svg.preset.interaction.list())
    assert "button" in dir(svg.rect(0, 0, 1, 1).interact)


def test_button_adds_a_hover_style_and_a_press_flash():
    doc = svg.Document(width=60, height=30)
    key = doc.rect(5, 5, 50, 20).interact.button(hover_opacity=0.5)
    text = doc.to_string()
    assert f"#{key.id}:hover {{ opacity:0.5 !important }}" in text
    assert re.search(rf'begin="{key.id}\.mousedown"', text)


def test_user_interactions_register_and_chain():
    @svg.preset.interaction
    def wobble(element, *, angle: float = 5) -> None:
        element.animate.on("hover").rotate(angle, dur=0.2)

    try:
        doc = svg.Document(width=40, height=40)
        dot = doc.circle(20, 20, 10).interact.wobble(angle=8).interact.highlight()
        assert dot.tag == "circle" and f"{dot.id}.mouseover" in doc.to_string()
    finally:
        svg.preset.interaction.unregister("wobble")


def test_unknown_interactions_suggest_a_name():
    with pytest.raises(AttributeError, match="did you mean 'button'"):
        svg.rect(0, 0, 1, 1).interact.buton()


def test_raw_svg_events_are_accepted():
    doc = svg.Document(width=40, height=40)
    dot = doc.circle(20, 20, 10)
    dot.animate.on("mousemove").fade_out(0.3)
    assert f'begin="{dot.id}.mousemove"' in doc.to_string()
    with pytest.raises(ValueError, match="SVG 1.1 event"):
        dot.animate.on("doubletap")
