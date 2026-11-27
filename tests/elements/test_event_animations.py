import re

import numpy as np
import pytest

import svgwriter as svg


def _begins(doc: svg.Document) -> list[str]:
    return re.findall(r'begin="([^"]+)"', doc.to_string())


def test_click_starts_the_preset_on_the_element_itself():
    doc = svg.Document(width=60, height=30)
    key = doc.rect(0, 0, 20, 20, id="key")
    key.animate.on("click").pulse(0.3)
    assert _begins(doc) and set(_begins(doc)) == {"key.click"}


def test_another_element_and_a_delay():
    doc = svg.Document(width=80, height=30)
    button = doc.rect(0, 0, 20, 20)
    ball = doc.circle(50, 10, 5)
    ball.animate.on("hover", button).fade_out(0.5, begin=0.25)
    text = doc.to_string()
    assert 'id="rect1"' in text and "rect1.mouseover+0.25s" in _begins(doc)


def test_presets_chain_and_multi_part_presets_follow():
    doc = svg.Document(width=80, height=30)
    word = doc.text("Hi", x=5, y=20)
    word.animate.on("click").create(1).fade_in(0.2)
    assert all(begin.startswith(f"{word.id}.click") for begin in _begins(doc))


def test_still_output_shows_the_resting_state():
    doc = svg.Document(width=40, height=40)
    dot = doc.circle(20, 20, 10, fill="black")
    dot.animate.on("click").fade_out(0.5)
    assert np.asarray(doc.at(2).rasterize())[20, 20, 3] == 1


def test_unknown_events_are_refused():
    with pytest.raises(ValueError, match="unknown event"):
        svg.circle(0, 0, 1).animate.on("doubletap")
