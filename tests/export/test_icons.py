from __future__ import annotations

import io

import numpy as np
import pytest

import svgwriter as svg


def logo() -> svg.Document:
    doc = svg.Document()
    doc.circle(0, 0, 10, fill="teal")
    doc.rect(-4, -4, 8, 8, fill="white")
    return doc


class TestExactSize:
    def test_square_fit_and_padding(self) -> None:
        wide = svg.Document(40, 10)
        wide.rect(0, 0, 40, 10, fill="red")
        pixels = wide.rasterize(size=(64, 64))
        assert pixels.shape == (64, 64, 4) and pixels[0, 32, 3] == 0 and pixels[32, 32, 3] == 1
        padded = logo().rasterize(size=(100, 100), padding=10)
        assert padded[50, 2, 3] == 0 and padded[50, 30, 3] == 1

    def test_size_as_int_for_raster_exports(self) -> None:
        png = logo().export("png", size=48, padding=1)
        assert int.from_bytes(png[16:20], "big") == 48 and int.from_bytes(png[20:24], "big") == 48


@pytest.mark.parametrize("fmt", ["svg", "png", "webp", "jpeg", "pdf", "ico", "icns", "eps", "tikz", "dxf"])
def test_output_is_deterministic(fmt: str) -> None:
    assert logo().export(fmt) == logo().export(fmt)


class TestIcons:
    def test_ico_reads_back(self, tmp_path) -> None:
        image_module = pytest.importorskip("PIL.Image")
        data = logo().export("ico", sizes=(16, 32, 256))
        icon = image_module.open(io.BytesIO(data))
        assert icon.format == "ICO" and sorted(icon.info["sizes"]) == [(16, 16), (32, 32), (256, 256)]
        (tmp_path / "a.ico").write_bytes(data)
        back = svg.Document.open(tmp_path / "a.ico")
        assert back[0].shape == (256, 256)

    def test_icns_reads_back(self, tmp_path) -> None:
        image_module = pytest.importorskip("PIL.Image")
        data = logo().export("icns", sizes=(16, 32, 512))
        icon = image_module.open(io.BytesIO(data))
        assert icon.format == "ICNS" and data[:4] == b"icns" and int.from_bytes(data[4:8], "big") == len(data)
        (tmp_path / "a.icns").write_bytes(data)
        back = svg.Document.open(tmp_path / "a.icns")
        assert back[0].shape == (512, 512) and np.allclose(back[0].color[256, 256], (1, 1, 1), atol=0.02)

    def test_invalid_sizes(self) -> None:
        with pytest.raises(ValueError, match="1..256"):
            logo().export("ico", sizes=(512,))
        with pytest.raises(ValueError, match="ICNS sizes"):
            logo().export("icns", sizes=(20,))


@pytest.mark.parametrize("size", [(480, 360), (481, 359), (17, 1000), (1000, 3)])
def test_exact_size_has_no_round_off(size: tuple[int, int]) -> None:
    doc = svg.Document(root=svg.Svg(view_box=(0, 0, 480, 360), width="100%", height="100%"))
    doc.rect(0, 0, 480, 360)
    assert doc.rasterize(size=size).shape[:2] == (size[1], size[0])
