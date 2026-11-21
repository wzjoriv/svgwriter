"""Themes and layout together: role backgrounds, role styles that size stacked text, theme switches and exports."""

import io

import pytest

import svgwriter as svg

from .conftest import card

EMU_PER_PX = 9525


def test_surface_background_and_child_roles_are_written():
    doc, stack = card()
    text = doc.to_string()
    assert stack.background.classes == ["role-surface"]
    for role in ("surface", "title", "text", "accent"):
        assert f".role-{role}" in text


def test_stacked_text_is_measured_with_the_theme_role_size():
    doc, stack = card()
    title = stack[1]
    themed = doc.theme.replace(fonts={"sizes": {"title": 48}})
    small = svg.parse(doc.to_string()).find(svg.Rect)
    doc.theme = themed
    large = svg.parse(doc.to_string()).find(svg.Rect)
    assert title.get("font-size") is None
    assert float(large.get("height")) > float(small.get("height"))


def test_text_without_a_font_size_stacks_at_the_default_size():
    a, b = svg.text("one"), svg.text("two")
    svg.VStack(a, b, gap=2)
    assert b.bounds().y > a.bounds().y + a.bounds().height


@pytest.mark.parametrize("theme", ["dark", "print"])
def test_theme_switch_restyles_without_moving_shapes(theme):
    doc, stack = card()
    bar = stack[3]
    before = bar.bounds()
    doc.theme = theme
    text = doc.to_string()
    assert svg.themes.get(theme).palette.surface.hex in text
    assert bar.bounds().x == before.x


@pytest.mark.parametrize("theme", ["dark", "print"])
def test_exports_place_the_laid_out_shapes_alike(theme):
    pptx = pytest.importorskip("pptx")
    doc = svg.Document(200, 100, theme=theme)
    first, second = svg.rect(0, 0, 40, 10).as_role("accent"), svg.rect(0, 0, 20, 10).as_role("shape")
    stack = svg.HStack(first, second, gap=10, padding=5, background="surface").translate(20, 30)
    doc += stack
    expected = [20.0, 30.0, 80.0, 20.0, 25.0, 35.0, 40.0, 10.0, 75.0, 35.0, 20.0, 10.0]

    pdf = svg.Document.from_string(doc.export("pdf"), "pdf")
    boxes = [path.bounds() for path in pdf.root.iter("path")]
    assert [v for b in boxes for v in (b.x, b.y, b.width, b.height)] == pytest.approx(expected)

    slide = pptx.Presentation(io.BytesIO(doc.export("pptx"))).slides[0]
    placed = [v / EMU_PER_PX for s in slide.shapes for v in (s.left, s.top, s.width, s.height)]
    assert placed == pytest.approx(expected)

    pixels = doc.rasterize()
    background = pixels[0, 0]
    accent = svg.themes.get(theme).palette.accent
    assert tuple(pixels[40, 45, :3]) == pytest.approx(accent.rgb, abs=1 / 255)
    assert tuple(pixels[25, 10]) == pytest.approx(tuple(background), abs=1e-6)


def test_bounds_before_output_agree_with_the_output():
    doc, stack = card()
    title = stack[1]
    height = title.bounds().height
    doc.theme = doc.theme.replace(fonts={"sizes": {"title": 48}})
    assert title.bounds().height > height
    written = svg.parse(doc.to_string()).find(svg.Rect)
    box = stack.background.bounds()
    assert (float(written.get("width")), float(written.get("height"))) == pytest.approx((box.width, box.height), abs=1e-3)
