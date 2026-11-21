from __future__ import annotations

import math

import numpy as np
import pytest

import svgwriter as svg


def area(element) -> float:
    pixels = element.rasterize(scale=1)
    return float(pixels[..., 3].sum())


class TestGroupOutlines:
    def test_union_of_children_with_their_transforms(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 10, 10), svg.Rect(0, 0, 10, 10).translate(5, 0))
        assert g.exact_bbox() == (0, 0, 15, 10)

    def test_group_transform_applies(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 10, 10)).translate(100, 0)
        assert g.to_path().bounds() == (100, 0, 10, 10)

    def test_boolean_ops_on_groups(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 10, 10), svg.Rect(20, 0, 10, 10))
        cut = g - svg.Rect(5, 0, 20, 10)
        assert isinstance(cut, svg.Path) and cut.exact_bbox() == (0, 0, 30, 10)
        assert math.isclose(cut.to_path().total_length(), 2 * (5 + 10) * 2)

    def test_text_in_group(self) -> None:
        g = svg.Group(svg.Text("Hi", x=0, y=20, font_size=20))
        assert g.to_path().exact_bbox().width > 5

    def test_nested_and_empty(self) -> None:
        assert len(svg.Group().to_path().d) == 0
        g = svg.Group(svg.Group(svg.Circle(5, 5, 5)), svg.Title("t"), svg.Defs(svg.Rect(0, 0, 99, 99)))
        assert g.exact_bbox() == pytest.approx((0, 0, 10, 10))

    def test_image_in_group_is_a_clear_error(self) -> None:
        with pytest.raises(TypeError, match="<image> has no vector outline"):
            svg.Group(svg.Image("a.png", 0, 0, 5, 5)).to_path()

    def test_use_outline(self) -> None:
        doc = svg.Document(50, 50)
        r = doc.define(svg.Rect(0, 0, 4, 4, id="r"))
        u = doc.use(r, x=10)
        assert u.exact_bbox() == (10, 0, 4, 4)
        with pytest.raises(TypeError, match="refers to nothing"):
            svg.Use().to_path()


class TestConversions:
    def test_image_to_path_raises_with_hint(self) -> None:
        with pytest.raises(TypeError, match="rasterize"):
            svg.Image("a.png", 0, 0, 5, 5).to_path()

    def test_to_group(self) -> None:
        c = svg.Circle(5, 5, 2, fill="red")
        g = c.to_group(opacity=0.5)
        assert isinstance(g, svg.Group) and g[0] is not c and g[0].get("fill") == "red" and g.get("opacity") == 0.5
        assert svg.Group(id="x").to_group() is not None

    def test_to_path_copies_presentation_and_drops_geometry(self) -> None:
        p = svg.Circle(5, 5, 2, fill="red", id="c").translate(1).to_path()
        assert p.get("fill") == "red" and not p.has("cx") and not p.has("id") and not p.has("transform")


class TestClip:
    def test_clip_sets_reference_and_defines(self) -> None:
        doc = svg.Document(100, 100)
        art = doc.rect(0, 0, 100, 100, fill="teal").clip(svg.Circle(50, 50, 40))
        assert art.clip_region is doc.defs[0] and "clip-path=\"url(#" in doc.to_string()

    def test_clip_multiple_shapes_and_existing_clip_path(self) -> None:
        cp = svg.ClipPath(svg.Rect(0, 0, 1, 1))
        assert svg.Rect().clip(cp).clip_region is cp
        assert len(svg.Rect().clip(svg.Circle(), svg.Rect()).clip_region) == 2

    def test_clip_on_group_and_text(self) -> None:
        assert svg.Group().clip(svg.Circle(0, 0, 1)).clip_region is not None
        assert svg.Text("x").clip(svg.Circle(0, 0, 1)).clip_region is not None

    def test_unclip_and_errors(self) -> None:
        r = svg.Rect().clip(svg.Circle())
        assert r.unclip().clip_region is None
        with pytest.raises(TypeError, match="unclip"):
            svg.Rect().clip()

    def test_flatten_clip_intersects(self) -> None:
        r = svg.Rect(0, 0, 100, 100, fill="teal").clip(svg.Rect(50, 0, 100, 100))
        flat = r.flatten_clip()
        assert flat.exact_bbox() == (50, 0, 50, 100) and not flat.has("clip-path") and flat.get("fill") == "teal"

    def test_clip_moves_with_element(self) -> None:
        r = svg.Rect(0, 0, 10, 10).clip(svg.Rect(0, 0, 5, 10)).translate(100)
        assert r.to_path().exact_bbox() == (100, 0, 5, 10)

    def test_object_bounding_box_units(self) -> None:
        r = svg.Rect(10, 10, 20, 20).clip(svg.Rect(0, 0, 0.5, 1), units="objectBoundingBox")
        assert r.to_path().exact_bbox() == (10, 10, 10, 20)

    def test_clip_by_id_in_document(self) -> None:
        doc = svg.Document.from_string(
            '<svg xmlns="http://www.w3.org/2000/svg"><defs><clipPath id="c"><rect width="5" height="5"/></clipPath></defs>'
            '<rect width="10" height="10" clip-path="url(#c)"/></svg>'
        )
        assert doc.root.find(svg.Rect).to_path().exact_bbox() == (0, 0, 5, 5)

    def test_clipped_group_rasterizes_smaller(self) -> None:
        full = svg.Rect(0, 0, 20, 20, fill="black")
        clipped = svg.Rect(0, 0, 20, 20, fill="black").clip(svg.Rect(0, 0, 10, 20))
        assert area(clipped) == pytest.approx(area(full) / 2, rel=0.02)


class TestRasterizeElement:
    def test_shape_and_scale(self) -> None:
        pixels = svg.Rect(0, 0, 8, 4, fill="red").rasterize(scale=2)
        assert pixels.shape == (8, 16, 4) and np.allclose(pixels[4, 8], (1, 0, 0, 1))

    def test_bounds_include_transform_and_stroke(self) -> None:
        r = svg.Rect(0, 0, 10, 10, fill="red", stroke="black", stroke_width=4).translate(500, 500)
        assert r.rasterize().shape == (14, 14, 4)

    def test_padding_and_background(self) -> None:
        pixels = svg.Circle(5, 5, 5, fill="red").rasterize(padding=2, background="white")
        assert pixels.shape == (14, 14, 4) and np.allclose(pixels[0, 0], 1)

    def test_uses_unplaced_and_document_definitions(self) -> None:
        grad = svg.LinearGradient.horizontal("blue", "blue")
        loose = svg.Rect(0, 0, 4, 4, fill=grad)
        assert loose.rasterize()[2, 2, 2] == pytest.approx(1) and grad.parent is None
        doc = svg.Document(10, 10)
        placed = doc.rect(0, 0, 4, 4, fill=svg.LinearGradient.horizontal("lime", "lime"))
        assert placed.rasterize()[2, 2, 1] == pytest.approx(1)

    def test_unknown_size_errors(self) -> None:
        with pytest.raises(TypeError, match="no known size"):
            svg.Image("a.png").rasterize()

    def test_group(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 2, 2, fill="red"), svg.Rect(4, 0, 2, 2, fill="blue"))
        assert g.rasterize().shape == (2, 6, 4)


class TestClone:
    def test_deep_clone_is_independent(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 1, 1, fill="red"), id="g").rotate(10)
        c = g.clone()
        assert type(c) is svg.Group and c is not g and c[0] is not g[0] and c.parent is None
        c[0].fill = "blue"
        c.translate(5)
        assert str(g[0].get("fill")) == "red" and str(g.t) == "rotate(10 0.5 0.5)"

    def test_clone_copies_pixels_and_anchor(self) -> None:
        img = svg.Image(np.zeros((2, 2, 3)), anchor=(0, 0))
        c = img.clone()
        c.color[0, 0] = 1
        assert img.color.max() == 0 and c.anchor == (0, 0)

    def test_linked_clone_is_a_use(self) -> None:
        doc = svg.Document(20, 20)
        r = doc.rect(0, 0, 4, 4, fill="red")
        u = r.clone(linked=True) + (10, 0)
        doc += u
        assert isinstance(u, svg.Use) and u.target == r.id and r.parent is doc.root
        r.width = 6
        assert u.exact_bbox() == (10, 0, 6, 4)

    def test_linked_clone_of_unplaced_element_goes_to_defs(self) -> None:
        doc = svg.Document(20, 20)
        star = svg.Circle(0, 0, 2)
        doc += star.clone(linked=True)
        assert star.parent is doc.defs

    def test_copy_module(self) -> None:
        import copy

        r = svg.Rect(fill="red")
        assert copy.copy(r) is not r and copy.deepcopy(r).get("fill") == r.get("fill")


class TestUseAppearance:
    def test_target_style_wins_and_use_style_is_inherited(self) -> None:
        doc = svg.Document(20, 20)
        r = doc.define(svg.Rect(0, 0, 2, 2, fill="red"))
        u = doc.use(r, x=5, stroke="blue", fill="green")
        p = u.to_path()
        assert str(p.get("fill")) == "red" and str(p.get("stroke")) == "blue"
        assert p.exact_bbox() == (5, 0, 2, 2) and not p.has("xlink:href") and not p.has("x")

    def test_target_transform_applies_but_not_its_parents(self) -> None:
        doc = svg.Document(20, 20)
        g = doc.group().translate(100, 100)
        r = svg.Rect(0, 0, 2, 2, id="r").translate(1, 0)
        g += r
        u = doc.use(r)
        assert u.exact_bbox() == (1, 0, 2, 2)


def test_copy_is_clone() -> None:
    r = svg.Rect(fill="red")
    assert svg.Rect.copy is svg.Rect.clone and r.copy() is not r and r.copy(linked=True).tag == "use"


def test_element_rasterize_size_fits_and_centres():
    import svgwriter as svg

    pixels = svg.rect(0, 0, 8, 4, fill="red").rasterize(pixels=32)
    assert pixels.shape == (32, 32, 4)
    assert pixels[16, 16, 3] == 1.0 and pixels[2, 16, 3] == 0.0
    assert svg.rect(0, 0, 8, 4).rasterize(pixels=(20, 10)).shape == (10, 20, 4)
