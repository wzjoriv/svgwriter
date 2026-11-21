from __future__ import annotations

import pytest

import svgwriter as svg


def starts(**spacing: object) -> list[float]:
    return [box.x for box in svg.text("a b", x=0, y=20, font_size=20, **spacing).layout()]


@pytest.mark.parametrize("value, step", [(3, 3.0), ("-1", -1.0), ("0.5em", 10.0), ("normal", 0.0)])
def test_letter_spacing_follows_every_character(value: object, step: float) -> None:
    plain, spaced = starts(), starts(letter_spacing=value)
    assert spaced[1] - plain[1] == pytest.approx(step)
    assert spaced[2] - plain[2] == pytest.approx(2 * step)


def test_word_spacing_follows_spaces_only() -> None:
    plain, spaced = starts(), starts(word_spacing=5)
    assert spaced[1] == pytest.approx(plain[1])
    assert spaced[2] - plain[2] == pytest.approx(5.0)


@pytest.mark.parametrize("size, style", [(24, None), (None, "font-size:24px")])
def test_em_positions_use_the_text_own_font_size(size: float | None, style: str | None) -> None:
    group = svg.group(font_size=18)
    text = group.add(svg.text("a", x=0, y="2em", font_size=size, style=style))
    assert text.layout()[0].y == pytest.approx(48.0)
