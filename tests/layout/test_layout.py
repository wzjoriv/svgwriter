"""Stacks and grids: placement for every alignment, gaps, padding, tracks, nesting, re-layout, units and export."""

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.layout._tracks import auto_place, parse_tracks, size_tracks


def boxes(*sizes):
    return [svg.rect(0, 0, w, h) for w, h in sizes]


def corner(element):
    box = element.bounds()
    return (round(box.x, 6), round(box.y, 6))


@pytest.mark.parametrize(("align", "xs"), [("start", [0, 0]), ("center", [0, 5]), ("end", [0, 10])])
def test_vstack_aligns_across(align, xs):
    a, b = boxes((20, 4), (10, 4))
    svg.VStack(a, b, gap=3, align=align)
    assert [corner(a), corner(b)] == [(xs[0], 0), (xs[1], 7)]


@pytest.mark.parametrize(("align", "ys"), [("start", [0, 0]), ("center", [0, 3]), ("end", [0, 6])])
def test_hstack_aligns_across(align, ys):
    a, b = boxes((5, 10), (5, 4))
    svg.HStack(a, b, gap=2, align=align)
    assert [corner(a), corner(b)] == [(0, ys[0]), (7, ys[1])]


def test_stretch_resizes_rects_and_skips_other_shapes():
    a, b = boxes((20, 4), (10, 4))
    dot = svg.circle(0, 0, 2)
    svg.VStack(a, b, dot, align="stretch")
    assert b.bounds().width == 20 and dot.bounds().width == 4 and corner(dot) == (0, 8)


def test_stretch_restores_the_natural_size_when_the_stack_shrinks():
    wide, narrow = boxes((30, 4), (10, 4))
    stack = svg.VStack(wide, narrow, align="stretch")
    assert narrow.bounds().width == 30
    wide.width = 12
    assert stack.bounds().width == 12 and narrow.bounds().width == 12
    stack.align_items = "start"
    assert narrow.bounds().width == 10


@pytest.mark.parametrize(("justify", "xs"), [
    ("start", [0, 10, 20]), ("center", [20, 30, 40]), ("end", [40, 50, 60]),
    ("space_between", [0, 30, 60]), ("space_around", [20 / 3, 30, 160 / 3]), ("space_evenly", [10, 30, 50]),
])
def test_hstack_distributes_along(justify, xs):
    items = boxes((10, 5), (10, 5), (10, 5))
    svg.HStack(*items, width=70, justify=justify)
    assert [corner(item)[0] for item in items] == pytest.approx(xs)


def test_vstack_justifies_vertically_and_overflow_falls_back():
    a, b = boxes((5, 10), (5, 10))
    svg.VStack(a, b, height=40, justify="end")
    assert corner(a) == (0, 20)
    c, d = boxes((5, 10), (5, 10))
    svg.VStack(c, d, height=10, justify="space_evenly")
    assert corner(c) == (0, -5)


@pytest.mark.parametrize(("padding", "expected"), [
    (2, (2, 2, 14, 14)), ((1, 3), (3, 1, 16, 12)), ((1, 2, 3, 4), (4, 1, 16, 14)),
])
def test_padding_forms(padding, expected):
    (a,) = boxes((10, 10))
    stack = svg.VStack(a, padding=padding)
    box = stack.bounds()
    assert (*corner(a), box.width, box.height) == expected


def test_gap_spacer_and_fixed_size():
    a, b, c = boxes((10, 10), (10, 10), (10, 10))
    row = svg.HStack(a, svg.Spacer(), b, svg.Spacer(2), c, width=100, gap=5)
    assert [corner(a)[0], corner(b)[0], corner(c)[0]] == pytest.approx([0, 20 + 50 / 3, 90])
    assert row.bounds().width == 100


def test_background_role_shape_and_scaled_shape():
    (a,) = boxes((20, 10))
    card = svg.VStack(a, padding=5, background="surface")
    assert card.background.classes == ["role-surface"] and card.background.bounds() == card.bounds()
    card.background = svg.ellipse(0, 0, 1, 1)
    assert card.background.bounds() == svg.BBox(0, 0, 30, 20)
    card.background = None
    assert len(card) == 1


def test_text_is_measured_by_its_line_box():
    labels = [svg.text(t, font_size=20) for t in "7-"]
    row = svg.HStack(*labels, gap=4)
    first, second = (svg.layout._measure.text_box(t) for t in labels)
    assert first.height == second.height
    assert row.bounds().height == pytest.approx(first.height)
    assert labels[1].bounds().x > labels[0].bounds().x


def test_tracks_parse_and_size():
    assert parse_tracks("auto 2fr 4mm")[2].fixed == pytest.approx(svg.mm(4).to_user_units())
    assert size_tracks(parse_tracks("auto 1fr 2fr"), [5, 0, 0], [], 35, 0) == [5, 10, 20]
    assert size_tracks(parse_tracks("1fr 1fr"), [40, 0], [], 50, 0) == [40, 10]
    assert size_tracks(parse_tracks("auto auto"), [5, 5], [(0, 2, 20)], None, 2) == [9, 9]
    assert auto_place([(3, 1), (1, 1)], 2) == [(0, 0), (0, 1)]
    with pytest.raises(ValueError):
        parse_tracks("0fr")


def test_grid_fixed_auto_and_fr_tracks():
    a, b, c = boxes((5, 5), (12, 5), (5, 5))
    grid = svg.Grid(a, b, c, columns=[20, "auto", "1fr"], rows=["auto"], width=60, gap=(2, 0), justify="start")
    assert [corner(x)[0] for x in (a, b, c)] == [0, 22, 36]
    assert grid.bounds().width == 60


def test_grid_cells_align_and_span():
    keys = boxes(*[(10, 10)] * 5)
    grid = svg.Grid(*keys, columns=3, gap=2, align="center")
    grid.span(keys[3], columns=2)
    assert keys[3].bounds() == svg.BBox(0, 12, 22, 10)
    grid.justify_items = "center"
    dot = grid.add(svg.circle(0, 0, 2))
    assert corner(dot) == (3, 27)
    with pytest.raises(ValueError):
        grid.span(svg.rect(0, 0, 1, 1))


def test_grid_rows_and_implicit_rows():
    items = boxes(*[(4, 4)] * 5)
    grid = svg.Grid(*items, columns=2, rows=[10])
    assert grid.bounds().height == 18
    grid.columns = 5
    assert grid.bounds().height == 10


def test_nested_layouts_stretch_and_follow_changes():
    label = svg.text("Key", font_size=12)
    key = svg.VStack(label, padding=4, background=svg.rect(rx=3))
    other = svg.VStack(svg.text("Other key", font_size=12), padding=4, background=svg.rect(rx=3))
    grid = svg.Grid(key, other, columns=2, gap=4)
    card = svg.VStack(svg.rect(0, 0, 200, 10), grid, gap=8, padding=10, align="stretch", background="surface")
    assert key.bounds().width == other.bounds().width == pytest.approx(98)
    assert key.background.get("width") == pytest.approx(98)
    grid.gap = 20
    assert key.bounds().width == pytest.approx(90)
    label.text_content = "A much longer label than before"
    assert key.bounds().width > 90 and card.bounds().width > 220


def test_relayout_after_adding_a_child_and_reading_bounds():
    stack = svg.VStack(*boxes((10, 10)), gap=2)
    late = stack.add(svg.rect(0, 0, 10, 10))
    assert corner(late) == (0, 12)
    stack.insert(0, svg.rect(0, 0, 10, 5))
    assert corner(late) == (0, 19)


def test_units_follow_the_document_scale():
    doc = svg.Document(size="a6-landscape")
    a, b = boxes((10, 10), (10, 10))
    stack = doc.add(svg.VStack(a, b, gap=svg.mm(2), padding="1cm"))
    assert corner(b) == pytest.approx((10, 22))
    assert stack.bounds().height == pytest.approx(42)
    assert svg.VStack(*boxes((1, 1), (1, 1)), gap="1in").bounds().height == pytest.approx(98)
    with pytest.raises(ValueError):
        svg.VStack(gap="10%").bounds()


def test_invalid_names_are_reported():
    with pytest.raises(ValueError, match="space_between"):
        svg.HStack(justify="between")
    with pytest.raises(ValueError, match="stretch"):
        svg.Grid(columns=2, align="middle")
    with pytest.raises(ValueError):
        svg.VStack(padding=(1, 2, 3))


def test_output_is_plain_groups_and_clones_keep_layout():
    a, b = boxes((10, 10), (10, 10))
    card = svg.HStack(a, b, gap=4, background="surface")
    text = str(card)
    assert "translate(14)" in text and "foreignObject" not in text
    twin = card.clone()
    twin.gap = 10
    assert twin[2].bounds().x == 20 and b.bounds().x == 14
    assert svg.parse(text).tag == "g"


def _keypad() -> svg.Document:
    keys = [svg.VStack(svg.text(k, font_size=14), padding=6, align="center", background=svg.rect(fill="teal"))
            for k in "123456"]
    doc = svg.Document(120, 80)
    doc += svg.Grid(*keys, columns=3, gap=4, padding=4, background=svg.rect(fill="#eee")).translate(10, 5)
    return doc


@pytest.mark.parametrize("fmt", ["pdf", "pptx"])
def test_exporters_keep_positions(fmt):
    if fmt == "pptx":
        pytest.importorskip("pptx")
    original = _keypad()
    data = svg.export.export(original, fmt)
    back = svg.export.find_importer(fmt).function(data)
    if fmt == "pdf":
        back.root.set("viewBox", "0 0 120 80")
    back.root.set("width", 120)
    back.root.set("height", 80)
    render = [doc.rasterize(pixels=(120, 80), background="white")[..., :3] for doc in (original, back)]
    assert np.abs(render[0] - render[1]).mean() < 0.03


def test_rendering_uses_the_arranged_positions():
    doc = svg.Document()
    doc += svg.VStack(svg.text("Hi", font_size=20), svg.text("Hi", font_size=20), background=svg.rect(fill="red"))
    alpha = doc.rasterize()[..., 3]
    assert alpha[1:-1, 1:-1].min() > 0.9


def test_laying_out_twice_changes_nothing():
    doc = _keypad()
    first = doc.to_string()
    assert doc.to_string() == first
