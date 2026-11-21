"""Batches: broadcasting, colours, markup equal to element-by-element output, expansion and editing."""

import numpy as np
import pytest

import svgwriter as svg

RNG = np.random.default_rng(7)


def looped(batch):
    """The same items made one by one with the element classes, in a group like the batch's ``<g>``."""
    group = svg.Group(attrs=dict(batch.attributes))
    for item in batch.clone().items:
        group.add(item.clone())
    return group


def pixels(element):
    doc = svg.Document(120, 120)
    doc += element.clone()
    return doc.rasterize()


@pytest.mark.parametrize("make", [
    lambda: svg.batch.circles(RNG.uniform(0, 99, 20), RNG.uniform(0, 99, 20), RNG.uniform(1, 3, 20)),
    lambda: svg.batch.points(np.arange(5.5, step=0.5), -1.25, 3, fill="red"),
    lambda: svg.batch.rects(RNG.uniform(0, 99, 8), 2, 5.5, [[1], [2]], rx=1, stroke="navy"),
    lambda: svg.batch.lines(0, 0, RNG.normal(size=6), RNG.normal(size=6), stroke_width=[1, 2, 3, 1, 2, 3]),
    lambda: svg.batch.polylines([RNG.uniform(0, 9, (k, 2)) for k in (1, 2, 7)], closed=True),
    lambda: svg.batch.texts(["a", "b & c", "<d>"], [0, 10, 20], 5, font_size=7, text_anchor="middle"),
])
def test_compact_markup_matches_elements_made_one_by_one(make):
    batch = make()
    assert batch.to_string(pretty=False) == looped(batch).to_string(pretty=False)
    assert batch.to_string() == batch.clone().expand().to_string()


@pytest.mark.parametrize("make", [
    lambda: svg.batch.instances(svg.rect(0, 0, 4, 2, id="tile"), [20, 60], 30, angle=[0, 45], scale=3),
    lambda: svg.batch.circles(RNG.uniform(10, 99, 9), 50, 6, fill=["red", "blue", "green"] * 3).rotate(30).scale(
        [1, 2, 1] * 3),
    lambda: svg.batch.texts(["ab", "cd"], [20, 60], 50, font_size=20).rotate([0, 90]),
])
def test_compact_and_expanded_batches_draw_the_same(make):
    batch = make()
    np.testing.assert_allclose(pixels(batch), pixels(batch.clone().expand()), atol=0.05)


def test_arguments_broadcast_with_numpy_rules():
    x, y = np.meshgrid(np.arange(4), np.arange(3))
    batch = svg.batch.circles(x, y, np.arange(4), fill=svg.batch.colormap("viridis", x))
    assert len(batch) == 12
    assert batch.column("r").tolist() == np.broadcast_to(np.arange(4), (3, 4)).ravel().tolist()
    with pytest.raises(ValueError, match="do not broadcast"):
        svg.batch.circles([1, 2, 3], [1, 2], 1)


@pytest.mark.parametrize(("fill", "expected", "alpha"), [
    (["red", "#00ff00"], ["#ff0000", "#00ff00"], None),
    (np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]), ["#ff0000", "#0000ff"], None),
    (np.array([[255, 0, 0, 255], [0, 0, 255, 51]]), ["#ff0000", "#0000ff"], [1.0, 0.2]),
    ([svg.Color.parse("#00000080"), "white"], ["#000000", "#ffffff"], [128 / 255, 1.0]),
])
def test_colour_columns(fill, expected, alpha):
    batch = svg.batch.circles([0, 1], 0, 1, fill=fill)
    assert batch.column("fill").tolist() == expected
    if alpha is None:
        assert "fill-opacity" not in batch.item_attributes
    else:
        assert batch.column("fill_opacity").tolist() == pytest.approx(alpha)


def test_one_value_for_all_sits_on_the_group_when_inherited():
    batch = svg.batch.circles([0, 1], 0, 1, fill="teal", opacity=0.5, stroke_dasharray=[2, 1])
    assert batch.attributes["fill"] == "teal" and batch.get("stroke-dasharray") == [2, 1]
    assert batch.get("opacity") is None and batch.column("opacity").tolist() == [0.5, 0.5]


def test_colormaps():
    assert svg.batch.colormap("grays", [0, 1, 2]).tolist() == [[0, 0, 0], [0.5, 0.5, 0.5], [1, 1, 1]]
    assert svg.batch.colormap("magma", [5], vmin=0, vmax=1)[0] == pytest.approx(svg.Color.parse("#fcfdbf").rgba[:3])
    assert set(svg.batch.colormaps()) >= {"viridis", "plasma", "inferno", "magma", "cividis", "turbo"}
    with pytest.raises(ValueError, match="viridis"):
        svg.batch.colormap("rainbow", [1])


def test_unknown_keywords_are_rejected():
    with pytest.raises(TypeError, match="fil"):
        svg.batch.circles(0, 0, 1, fil="red")


def test_indexing_expands_and_edits_stick():
    batch = svg.batch.circles([0, 10, 20], 0, 2, fill=["red", "green", "blue"])
    batch[1].r = 9
    batch[-1].fill = "black"
    assert not batch.compact and len(batch) == 3
    assert [item.r for item in batch] == [2.0, 9, 2.0]
    assert batch[1:] == batch.items[1:]
    assert '<circle cx="20" cy="0" r="2" fill="black"/>' in batch.to_string()


def test_set_per_item_and_shared():
    batch = svg.batch.rects([0, 10], 0, 5, 5, fill=["red", "blue"])
    batch.set(fill="gold", width=[1, 2])
    assert batch.attributes["fill"] == "gold" and "fill" not in batch.item_attributes
    assert batch.column("width").tolist() == [1.0, 2.0]
    batch.set(width=None)
    assert "width" not in batch.item_attributes
    batch.expand().set(fill=["red", "blue"], opacity=0.5)
    assert [(item.get("fill"), item.opacity) for item in batch] == [("#ff0000", 0.5), ("#0000ff", 0.5)]
    batch.set(fill="black")
    assert batch.attributes["fill"] == "black" and all(item.get("fill") is None for item in batch)
    with pytest.raises(ValueError, match="one value per item"):
        batch.set(stroke_width=[1, 2, 3])


@pytest.mark.parametrize("about", [None, (5, 5)])
def test_vectorized_transforms_match_element_transforms(about):
    batch = svg.batch.rects(RNG.uniform(0, 50, 6), RNG.uniform(0, 50, 6), 4, 2)
    elements = batch.clone().expand()
    for target in (batch, elements):
        target.translate(np.arange(6), 1).rotate(np.arange(6) * 15, about=about).scale([1, 2, 1, 2, 1, 2], about=about)
    assert batch.compact
    np.testing.assert_allclose(batch.column("transform"), elements.column("transform"), atol=1e-9)
    assert batch.bounds() == pytest.approx(elements.bounds())


def test_text_and_instance_items_turn_about_their_anchor_in_both_states():
    labels = svg.batch.texts(["a", "b"], [0, 10], 5).rotate(90)
    np.testing.assert_allclose(labels.column("transform"), labels.clone().expand().column("transform"))
    copies = svg.batch.instances(svg.circle(0, 0, 1), [5, 9], 1).scale(2)
    assert copies.bounds() == pytest.approx(svg.BBox(3, -1, 8, 4))
    copies.expand().rotate(30)
    assert copies.bounds().height > 4


def test_clones_share_nothing_mutable():
    batch = svg.batch.circles([0, 1], 0, 1)
    copy = batch.clone().set(r=[5, 6]).translate(1)
    assert batch.column("r").tolist() == [1.0, 1.0] and float(batch.column("transform")[0, 4]) == 0.0
    assert copy.column("r").tolist() == [5.0, 6.0]
    with pytest.raises(ValueError, match="read-only"):
        batch.column("cx")[0] = 3


def test_empty_batch():
    batch = svg.batch.circles([], [], 1)
    assert len(batch) == 0 and batch.bounds() is None
    assert batch.to_string(pretty=False, xml_declaration=False) == "<g/>"
