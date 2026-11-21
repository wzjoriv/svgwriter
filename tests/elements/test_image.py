from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.model.elements.structure import Pixels


class TestConstruction:
    def test_rgb_float_is_opaque_scalar_alpha(self) -> None:
        img = svg.Image(np.full((2, 3, 3), 0.5))
        assert img.color.shape == (2, 3, 3) and img.color.dtype == np.float32 and img.alpha == 1.0
        assert (img.width, img.height) == (3, 2) and img.shape == (2, 3)

    def test_rgba_uint8_splits_alpha(self) -> None:
        data = np.zeros((2, 2, 4), np.uint8)
        data[..., 3] = [[255, 0], [128, 255]]
        img = svg.Image(data)
        assert img.color.shape == (2, 2, 3) and img.alpha.shape == (2, 2, 1)
        assert img.alpha[1, 0, 0] == pytest.approx(128 / 255)

    def test_opaque_rgba_compacts_to_scalar(self) -> None:
        assert svg.Image(np.ones((2, 2, 4))).alpha == 1.0

    def test_grayscale_and_gray_alpha(self) -> None:
        g = svg.Image(np.linspace(0, 1, 6).reshape(2, 3))
        assert g.color.shape == (2, 3, 1)
        ga = svg.Image(np.zeros((2, 3, 2)))
        assert ga.color.shape == (2, 3, 1) and ga.alpha.shape == (2, 3, 1)
        assert g.rgba().shape == (2, 3, 4)

    @pytest.mark.parametrize("alpha", [0.5, np.full((2, 3), 0.5), np.full((2, 3, 1), 0.5), np.full((1, 3), 0.5)])
    def test_separate_alpha_broadcasts(self, alpha: object) -> None:
        img = svg.Image(np.zeros((2, 3, 3)), alpha=alpha)
        assert img.alpha.shape == (2, 3, 1) and np.allclose(img.alpha, 0.5)
        assert (img.color * img.alpha).shape == (2, 3, 3)

    def test_errors(self) -> None:
        with pytest.raises(ValueError, match="0..1"):
            svg.Image(np.full((2, 2, 3), 2.0))
        with pytest.raises(ValueError, match="shape"):
            svg.Image(np.zeros((2, 2, 5)))
        with pytest.raises(ValueError, match="twice"):
            svg.Image(np.zeros((2, 2, 4)), alpha=0.5)
        with pytest.raises(TypeError, match="numeric"):
            svg.Image(np.array([["a"]]))

    def test_explicit_size_is_kept(self) -> None:
        img = svg.Image(np.zeros((2, 2, 3)), 5, 6, 20, 10)
        assert img.bounds() == (5, 6, 20, 10)


class TestEditing:
    def test_in_place_and_assignment(self) -> None:
        img = svg.Image(np.zeros((2, 2, 3)))
        img.color[0, 0] = (1, 0, 0)
        img.alpha = np.array([[1, 0.5], [1, 1]])
        assert np.allclose(img.rgba()[0, 1, 3], 0.5) and np.allclose(img.rgba()[0, 0], (1, 0, 0, 1))
        img.color = np.ones((2, 2, 3), np.uint8) * 255
        assert np.allclose(img.color, 1) and img.alpha.shape == (2, 2, 1)

    def test_linked_image_has_no_pixels(self) -> None:
        img = svg.Image("pic.png", 0, 0, 10, 10)
        assert img.pixels is None and str(img.get("xlink:href")) == "pic.png"
        with pytest.raises(TypeError, match="Image.open"):
            _ = img.color


class TestRoundTrip:
    def test_written_as_png_data_uri_and_parsed_back_lazily(self) -> None:
        data = (np.arange(24, dtype=np.uint8).reshape(2, 3, 4) * 10)
        img = svg.Image(data)
        text = str(img)
        assert 'xlink:href="data:image/png;base64,' in text
        back = svg.parse(text)
        assert isinstance(back.pixels, Pixels) and np.allclose(back.rgba(), img.rgba(), atol=1 / 255)

    def test_unmodified_parsed_uri_is_written_verbatim(self) -> None:
        uri = svg.Image(np.zeros((1, 1, 3))).pixels.svg_value()
        img = svg.parse(f'<image xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="{uri}"/>')
        assert img.pixels is not None and img.pixels.svg_value() == uri

    def test_open_file_and_encode(self, tmp_path) -> None:
        path = tmp_path / "x.png"
        path.write_bytes(svg.Image(np.ones((3, 4, 3)) * 0.2).encode("png"))
        img = svg.Image.open(path, x=1)
        assert img.shape == (3, 4) and (img.x, img.width) == (1, 4) and np.allclose(img.color, 0.2, atol=0.01)
        assert img.encode("jpeg")[:2] == bytes.fromhex("ffd8")
        with pytest.raises(ValueError, match="decode"):
            Pixels.decode(b"junk")

    def test_renders_in_documents(self) -> None:
        doc = svg.Document(4, 4)
        doc += svg.Image(np.tile([0.0, 0.0, 1.0], (4, 4, 1)))
        assert np.allclose(svg.ops.rasterize(doc)[2, 2], (0, 0, 1, 1), atol=0.01)


class TestToImage:
    def test_rasterized_and_placed(self) -> None:
        c = svg.Circle(10, 10, 5, fill="red")
        img = c.to_image(scale=2)
        assert img.shape == (20, 20) and img.bounds() == (5, 5, 10, 10)
        assert np.allclose(img.color[10, 10], (1, 0, 0)) and img.alpha[0, 0, 0] == 0

    def test_opaque_background_compacts_alpha(self) -> None:
        assert svg.Rect(0, 0, 3, 3, fill="red").to_image(background="white", padding=1).alpha == 1.0

    def test_image_to_image(self) -> None:
        img = svg.Image(np.ones((2, 2, 3)), 0, 0, 2, 2)
        assert img.to_image().shape == (2, 2)


def blue(size: int = 4) -> svg.Image:
    return svg.Image(np.tile([0.0, 0.0, 1.0], (size, size, 1)))


class TestImageRendering:
    def test_z_order_vector_over_image_and_image_over_vector(self) -> None:
        doc = svg.Document(10, 4)
        doc.rect(0, 0, 10, 4, fill="red")
        doc += blue().place(4, 2)
        doc.rect(5, 0, 5, 4, fill="lime")
        px = svg.ops.rasterize(doc)
        assert np.allclose(px[2, 1], (1, 0, 0, 1)) and np.allclose(px[2, 3], (0, 0, 1, 1), atol=0.02)
        assert np.allclose(px[2, 7], (0, 1, 0, 1))

    def test_transform_opacity_and_group(self) -> None:
        doc = svg.Document(8, 8)
        g = doc.group(opacity=0.5)
        g += blue() + (4, 4)
        px = svg.ops.rasterize(doc)
        assert px[1, 1, 3] == 0 and np.isclose(px[6, 6, 3], 0.5, atol=0.02)

    def test_aspect_ratio_meet_and_none(self) -> None:
        doc = svg.Document(8, 4)
        doc += svg.Image(np.tile([0.0, 0.0, 1.0], (4, 4, 1)), 0, 0, 8, 4)
        px = svg.ops.rasterize(doc)
        assert px[2, 0, 3] == 0 and px[2, 4, 3] == pytest.approx(1)
        doc2 = svg.Document(8, 4)
        doc2 += svg.Image(np.tile([0.0, 0.0, 1.0], (4, 4, 1)), 0, 0, 8, 4, preserve_aspect_ratio="none")
        assert svg.ops.rasterize(doc2)[2, 0, 3] == pytest.approx(1)

    def test_view_box_scaling(self) -> None:
        doc = svg.Document(root=svg.Svg(view_box=(0, 0, 4, 4), width=8, height=8))
        doc += blue()
        assert svg.ops.rasterize(doc).shape == (8, 8, 4) and svg.ops.rasterize(doc)[7, 7, 3] == pytest.approx(1)

    def test_element_rasterize_with_image_inside(self) -> None:
        g = svg.Group(svg.Rect(0, 0, 8, 4, fill="red"), blue())
        px = g.rasterize()
        assert np.allclose(px[1, 1], (0, 0, 1, 1), atol=0.02) and np.allclose(px[1, 6], (1, 0, 0, 1))

    def test_rendering_leaves_document_untouched(self) -> None:
        doc = svg.Document(4, 4)
        r = doc.rect(0, 0, 1, 1)
        doc += blue()
        doc.circle(1, 1, 1)
        before = doc.to_string()
        svg.ops.rasterize(doc)
        assert doc.to_string() == before and not r.has("display")

    def test_clipped_image(self) -> None:
        doc = svg.Document(4, 4)
        doc += blue().clip(svg.Rect(0, 0, 2, 4))
        px = svg.ops.rasterize(doc)
        assert px[1, 0, 3] == pytest.approx(1) and px[1, 3, 3] == 0
