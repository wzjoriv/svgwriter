from __future__ import annotations

import gzip

import numpy as np
import pytest

import svgwriter as svg
from svgwriter import export


def drawing() -> svg.Document:
    doc = svg.Document(40, 20)
    doc.rect(0, 0, 40, 20, fill="red", id="bg")
    doc.link(href="https://example.org").add(svg.Circle(10, 10, 5, fill="blue"))
    return doc


class TestRegistry:
    def test_builtin_formats_and_lookup(self) -> None:
        names = set(export.exporters())
        assert {"svg", "svgz", "png", "jpeg", "webp", "pdf", "tikz", "eps"} <= names
        assert export.find_exporter("x/y/figure.JPG").name == "jpeg"
        assert export.find_exporter(".tex").name == "tikz" and export.find_exporter("PNG").name == "png"
        assert export.exporters()["png"].description

    def test_unknown_format(self) -> None:
        with pytest.raises(ValueError, match="known extensions"):
            export.find_exporter("figure.xyz")

    def test_register_custom_and_duplicates(self) -> None:
        @export.register("count-test", extensions=(".cnt",), binary=False, replace=True)
        def count(document, **options):
            """Number of top-level elements."""
            return str(len(document))

        assert drawing().export("count-test") == "2" and export.find_exporter("a.cnt").description.startswith("Number")
        with pytest.raises(ValueError, match="already registered"):
            export.register("count-test")(count)
        export.unregister("count-test")
        assert "count-test" not in export.exporters()
        with pytest.raises(KeyError, match="no exporter"):
            export.unregister("count-test")

    def test_save_and_open_round_trip(self, tmp_path) -> None:
        doc = drawing()
        for name in ("a.svg", "a.svgz", "a.png", "a.jpg", "a.webp", "a.pdf", "a.tex", "a.eps"):
            doc.save(tmp_path / name)
            assert (tmp_path / name).stat().st_size > 0
        assert gzip.decompress((tmp_path / "a.svgz").read_bytes()).startswith(b"<?xml")
        again = svg.Document.open(tmp_path / "a.svgz")
        assert again["bg"].tag == "rect" and 'href="https://example.org"' in again.to_string()
        image = svg.Document.open(tmp_path / "a.png")
        assert isinstance(image[0], svg.Image) and image[0].shape == (20, 40)
        assert np.allclose(image.rasterize()[2, 30], (1, 0, 0, 1), atol=0.02)

    def test_explicit_format_overrides_extension(self, tmp_path) -> None:
        drawing().save(tmp_path / "picture.bin", format="png")
        assert (tmp_path / "picture.bin").read_bytes()[:4] == bytes.fromhex("89504e47")

    def test_streams_still_write_svg(self) -> None:
        import io

        buffer = io.StringIO()
        drawing().save(buffer)
        assert buffer.getvalue().startswith("<?xml")


class TestFormats:
    def test_raster_options(self) -> None:
        doc = drawing()
        png = doc.export("png", scale=2)
        assert int.from_bytes(png[16:20], "big") == 80
        assert doc.export("jpeg", quality=50)[:2] == bytes.fromhex("ffd8")

    def test_pdf_is_vector_with_metadata(self) -> None:
        data = drawing().export("pdf", title="Figure 1")
        assert data.startswith(b"%PDF") and b"Figure 1" in data

    def test_tikz_standalone_and_colors(self) -> None:
        text = drawing().export("tikz", standalone=True)
        assert text.startswith(r"\documentclass[tikz]{standalone}")
        assert r"\definecolor{svgc0}{RGB}{255,0,0}" in text and "-- cycle" in text and ".. controls" in text

    def test_eps_header_and_flip(self) -> None:
        text = drawing().export("eps").decode()
        assert text.startswith("%!PS-Adobe-3.0 EPSF-3.0") and "%%BoundingBox: 0 0 40 20" in text
        assert "0 20 moveto" in text and text.rstrip().endswith("%%EOF")

    def test_formats_without_images_warn_about_them(self) -> None:
        doc = drawing()
        doc += svg.Image(np.zeros((2, 2, 3)))
        with pytest.warns(UserWarning, match="<image>"):
            doc.export("tikz")

    def test_flatten_transforms_opacity_and_paint_fallbacks(self) -> None:
        from svgwriter._internal._flatten import flatten

        doc = svg.Document(100, 100)
        g = doc.group(opacity=0.5).translate(10, 0)
        g.add(svg.Rect(0, 0, 10, 10, fill=svg.LinearGradient.horizontal("lime", "red"), stroke="black",
                       stroke_width=2)).scale(2, about=(0, 0))
        doc.rect(0, 0, 1, 1, fill="none", display="none")
        (item,) = flatten(doc).items
        assert item.data.bbox == (10, 0, 20, 20) and item.fill.hex == "#808000"
        assert item.fill_opacity == 0.5 and item.stroke_width == pytest.approx(4)
