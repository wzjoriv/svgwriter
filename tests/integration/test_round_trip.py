"""Saving and reopening a themed, laid-out, font-embedded SVG keeps its roles, positions, fonts and theme."""

import pytest

import svgwriter as svg

SIZE = 10


def themed_card(typeface: svg.Typeface, theme: svg.Theme | str) -> tuple[svg.Document, svg.VStack]:
    doc = svg.Document(200, 100, theme=theme)
    stack = svg.VStack(svg.text("AAA", font_family=typeface, font_size=SIZE).as_role("title"),
                       svg.rect(0, 0, 30, 5).as_role("accent"), gap=3, padding=4, background="surface")
    doc += stack
    doc.embed_fonts(typeface)
    return doc, stack


@pytest.mark.parametrize("theme", ["dark", svg.themes.get("paper").replace(name="brand", palette={"surface": "#123456"})])
def test_reopened_svg_keeps_roles_positions_fonts_and_theme(tmp_path, typeface, theme):
    doc, stack = themed_card(typeface, theme)
    placed = [child.bounds() for child in stack]
    doc.save(tmp_path / "card.svg")
    back = svg.Document.open(tmp_path / "card.svg")
    group = back.root.find(svg.Group)
    assert [child.get("class") for child in group] == ["role-surface", "role-title", "role-accent"]
    for child, box in zip(group, placed, strict=True):
        assert tuple(child.bounds()) == pytest.approx(tuple(box), abs=0.01)
    assert back.to_string() == doc.to_string()
    assert "@font-face" in back.to_string() and typeface.name in back.to_string()
    assert back.theme == svg.Theme.of(theme) if theme == "dark" else back.theme.name == "document"


def test_reopening_with_a_theme_restyles(tmp_path, typeface):
    doc, _ = themed_card(typeface, "dark")
    doc.save(tmp_path / "card.svg")
    light = svg.Document.open(tmp_path / "card.svg", theme="light")
    assert light.theme.name == "light"
    assert svg.themes.get("light").palette.surface.hex in light.to_string()
    with pytest.raises(TypeError, match="only theme="):
        svg.Document.open(tmp_path / "card.svg", palette="x")
