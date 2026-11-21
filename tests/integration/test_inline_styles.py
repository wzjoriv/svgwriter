"""Inkscape-style inline styles: assigning and reading a property goes where it takes effect."""

import pytest

import svgwriter as svg

INKSCAPE = ('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">'
            '<rect id="box" width="10" height="10" fill="#00ff00" '
            'style="fill:#ff0000;fill-opacity:1;stroke:#000000;stroke-width:2"/></svg>')


@pytest.fixture
def box():
    return svg.parse(INKSCAPE).find(svg.Rect)


def test_reading_returns_the_inline_value(box):
    assert str(box.fill) == "#ff0000" and box.get("stroke-width") == "2" and box.stroke_width == 2


def test_assigning_changes_the_inline_declaration(box):
    box.fill = "blue"
    box.stroke_width = 4
    assert box.style["fill"] == "blue" and box.style["stroke-width"] == 4
    assert box.attributes["fill"] == "#00ff00"
    assert svg.Color.parse(str(box.computed("fill"))) == svg.Color.parse("blue")


def test_alpha_goes_to_the_inline_opacity(box):
    box.fill = svg.Color(0, 0, 1, 0.5)
    assert box.style["fill-opacity"] == 0.5 and "fill-opacity" not in box.attributes


def test_none_removes_the_declaration_and_the_attribute(box):
    box.fill = None
    assert "fill" not in box.style and "fill" not in box.attributes
    for name in ("fill-opacity", "stroke", "stroke-width"):
        box.set(name, None)
    assert "style" not in box.attributes


def test_properties_without_a_declaration_stay_attributes(box):
    box.stroke_dasharray = "2 1"
    assert box.attributes["stroke-dasharray"] == "2 1" and "stroke-dasharray" not in box.style


def test_the_change_shows_in_the_rendered_pixels(box):
    doc = svg.Document(root=box.root())
    box.fill = "blue"
    pixels = doc.rasterize()
    assert tuple(pixels[5, 5, :3].round(2)) == (0.0, 0.0, 1.0)


def test_values_set_before_a_role_still_win_and_later_ones_follow_the_role():
    box = svg.rect(0, 0, 10, 10, stroke="red").as_role("box")
    box.stroke = "blue"
    box.fill = "green"
    assert box.style["stroke"] == "blue" and box.attributes["fill"] == "green"
    doc = svg.Document(10, 10)
    doc += box
    assert box.computed("stroke") == "blue"
