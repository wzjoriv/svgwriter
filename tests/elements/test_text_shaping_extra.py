"""Right-to-left anchoring and ASCII-safe notebook output."""

from __future__ import annotations

import pytest

import svgwriter as svg

URDU = "\u06c1\u06cc\u0644\u0648"


@pytest.mark.parametrize(("anchor", "side"), [("start", "right"), ("end", "left")])
def test_rtl_anchor_follows_the_text_direction(anchor: str, side: str) -> None:
    box = svg.text(URDU, x=100, y=40, font_size=24, direction="rtl", text_anchor=anchor).bounds()
    if side == "right":
        assert box.x + box.width <= 100.5
    else:
        assert box.x >= 99.5


def test_ltr_anchor_is_unchanged() -> None:
    assert svg.text("abc", x=100, y=40, font_size=24).bounds().x >= 99.5


def test_notebook_svg_is_ascii_and_keeps_the_text() -> None:
    doc = svg.Document(100, 30)
    doc.text("\u0928\u092e\u0938\u094d\u0924\u0947", x=5, y=20)
    markup = doc._repr_svg_()
    assert markup.isascii()
    back = svg.Document.from_string(markup)
    assert [e.text_content for e in back.root.iter() if e.tag == "text"] == ["\u0928\u092e\u0938\u094d\u0924\u0947"]
    assert svg.text("\u00e9t\u00e9", x=0, y=10)._repr_svg_().isascii()
