"""Batches with the rest of svgwriter: rendering, exporters, parsing, themes, animation and interpolation."""

import io
import zipfile

import numpy as np
import pytest

import svgwriter as svg


def scatter(count=40):
    rng = np.random.default_rng(3)
    x, y = rng.uniform(10, 90, (2, count))
    return svg.batch.circles(x, y, 3, fill=svg.batch.colormap("viridis", x), opacity=0.8)


def page(*elements):
    doc = svg.Document(100, 100)
    for element in elements:
        doc += element
    return doc


def test_rendering_keeps_the_batch_compact_and_draws_every_item():
    batch = scatter()
    doc = page(batch)
    drawn = doc.rasterize()
    assert batch.compact
    np.testing.assert_allclose(drawn, page(batch.clone().expand()).rasterize(), atol=1e-6)
    assert drawn[..., 3].sum() > 0


def test_text_batches_render_as_glyphs():
    labels = svg.batch.texts(["one", "two"], [10, 50], 50, font_size=16)
    assert page(labels).rasterize()[..., 3].sum() > 0 and labels.compact


def test_pptx_keeps_one_shape_per_item():
    data = page(scatter(12)).export("pptx")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        slide = archive.read("ppt/slides/slide1.xml").decode()
    assert slide.count("<p:sp>") == 12


@pytest.mark.parametrize("format", ["pdf", "eps", "tikz"])
def test_vector_exports_hold_every_item(format):
    small, large = page(scatter(5)).export(format), page(scatter(50)).export(format)
    assert len(large) > len(small)


def test_parsed_output_has_real_elements():
    batch = svg.batch.instances(svg.rect(0, 0, 2, 2), [10, 20, 30], 5, angle=[0, 10, 20])
    parsed = svg.parse(page(batch).to_string())
    assert [e.tag for e in parsed.iter() if e.tag == "use"] == ["use"] * 3
    assert 'xmlns:xlink="http://www.w3.org/1999/xlink"' in page(batch).to_string()


def test_theme_roles_style_the_batch():
    batch = scatter(3)
    batch.set(fill=None)
    batch.as_role("dot")
    doc = page(batch)
    doc.theme = "dark"
    text = doc.to_string()
    assert ".role-dot" in text and 'class="role-dot"' in text


def test_staggered_animation_per_item():
    batch = svg.batch.circles([10, 20, 30], 50, 4)
    batch.animate.fade_in(1, begin=np.array([0, 0.5, 1]), stagger=0.25)
    begins = [item.children[0].get("begin") for item in batch]
    assert begins == ["0s", "0.75s", "1.5s"]
    frame = page(batch).at(0.75)
    assert frame.root.find(svg.Circle).get("opacity") is not None


def test_show_and_hide_take_the_stagger_as_their_moment():
    batch = svg.batch.circles([10, 20], 50, 4)
    batch.animate.show(at=1, stagger=1)
    assert [item.children[0].get("begin") for item in batch] == ["1s", "2s"]


def test_interpolate_compact_batches_column_by_column():
    start = svg.batch.circles([0, 10], 0, 1, fill=["red", "blue"])
    end = start.clone().set(fill="white", r=[3, 5]).rotate(90).translate(10, 0)
    middle = svg.interpolate(start, end, 0.5)
    assert middle.compact and middle.get("fill") is None
    assert middle.column("r").tolist() == [2.0, 3.0]
    assert middle.column("fill").tolist() == ["#ff8080", "#8080ff"]
    turned = svg.interpolate(start.clone().expand(), end.clone().expand(), 0.5)
    np.testing.assert_allclose(middle.column("transform"), turned.column("transform"), atol=1e-9)
    assert svg.interpolate(start, svg.batch.circles(0, 0, 1), 0.75).column("cx").tolist() == [0.0]


def test_layout_measures_compact_batches():
    stack = svg.HStack(scatter(5), svg.rect(0, 0, 10, 10), gap=5)
    page(stack).to_string()
    assert stack.bounds().width > 10
