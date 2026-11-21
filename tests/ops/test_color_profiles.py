from __future__ import annotations

import base64
import struct
import sys
import warnings
import zlib

import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal import _icc
from svgwriter._internal._icc_embedded import embedded_profile
from svgwriter.elements.structure import Pixels

lcms2 = pytest.importorskip("lcms2")

SWATCH = (40, 150, 60)


def adobe() -> bytes:
    return lcms2.Profile("Adobe RGB (1998)").to_bytes()


def expected(profile: bytes, values: tuple[int, ...]) -> np.ndarray:
    out = lcms2.Profile.from_bytes(profile).transform(np.array(values, np.uint8), "sRGB")
    return np.asarray(out, np.float64) / 255


def png_with_profile(profile: bytes) -> bytes:
    png = svg.Image(np.tile(np.array(SWATCH, np.uint8), (4, 4, 1))).encode("png")
    body = b"adobe\x00\x00" + zlib.compress(profile)
    chunk = struct.pack(">I", len(body)) + b"iCCP" + body + struct.pack(">I", zlib.crc32(b"iCCP" + body))
    header_end = 8 + 25
    return png[:header_end] + chunk + png[header_end:]


def jpeg_with_profile(profile: bytes) -> bytes:
    jpeg = svg.Image(np.tile(np.array(SWATCH, np.uint8), (4, 4, 1))).encode("jpeg")
    body = b"ICC_PROFILE\x00\x01\x01" + profile
    return jpeg[:2] + b"\xff\xe2" + struct.pack(">H", len(body) + 2) + body + jpeg[2:]


def data_uri(data: bytes, kind: str = "application/vnd.iccprofile") -> str:
    return f"data:{kind};base64," + base64.b64encode(data).decode("ascii")


def icc_page(fill: str) -> svg.Document:
    doc = svg.Document(4, 4)
    doc.add(svg.ColorProfile("adobe", data_uri(adobe()), rendering_intent="relative-colorimetric"))
    doc.rect(0, 0, 4, 4, fill=fill)
    return doc


@pytest.fixture
def without_lcms(monkeypatch):
    monkeypatch.setitem(sys.modules, "lcms2", None)
    monkeypatch.setattr(_icc, "_HINTED", [])
    _icc.load_profile.cache_clear()
    yield
    _icc.load_profile.cache_clear()


def test_png_and_jpeg_profiles_are_found() -> None:
    profile = adobe()
    assert embedded_profile(png_with_profile(profile)) == profile
    assert embedded_profile(jpeg_with_profile(profile)) == profile
    assert embedded_profile(svg.Image(np.zeros((2, 2, 3))).encode("png")) is None


def test_icc_color_converts_through_named_profile() -> None:
    pixel = icc_page("black icc-color(adobe, 0.157, 0.588, 0.235)").rasterize()[2, 2, :3]
    assert np.allclose(pixel, expected(adobe(), SWATCH), atol=0.02)


def test_image_profile_by_url_reference() -> None:
    plain = svg.Image(np.tile(np.array(SWATCH, np.uint8), (4, 4, 1))).encode("png")
    doc = icc_page("none")
    doc.root.children[0].set("id", "adobe-profile")
    doc.add(svg.Image(data_uri(plain, "image/png"), 0, 0, 4, 4, color_profile="url(#adobe-profile)"))
    assert np.allclose(doc.rasterize()[2, 2, :3], expected(adobe(), SWATCH), atol=0.02)


def test_unknown_profile_uses_fallback() -> None:
    pixel = icc_page("#0000ff icc-color(missing, 1, 0, 0)").rasterize()[2, 2, :3]
    assert np.allclose(pixel, (0, 0, 1), atol=0.01)


def test_wrong_component_count_uses_fallback() -> None:
    assert np.allclose(icc_page("lime icc-color(adobe, 1)").rasterize()[2, 2, :3], (0, 1, 0), atol=0.01)


def test_color_with_icc_integrates() -> None:
    color = svg.Color.parse("black").with_icc("icc-color(adobe, 0.157, 0.588, 0.235)")
    pixel = icc_page(color).rasterize()[2, 2, :3]
    assert np.allclose(pixel, expected(adobe(), SWATCH), atol=0.02)


def test_embedded_png_profile_is_applied() -> None:
    decoded = Pixels.decode(png_with_profile(adobe()))
    assert np.allclose(decoded.color[0, 0], expected(adobe(), SWATCH), atol=0.02)


def test_image_color_profile_property(tmp_path) -> None:
    plain = svg.Image(np.tile(np.array(SWATCH, np.uint8), (4, 4, 1))).encode("png")
    (tmp_path / "swatch.png").write_bytes(plain)
    (tmp_path / "adobe.icc").write_bytes(adobe())
    doc = svg.Document(4, 4)
    doc.add(svg.ColorProfile("adobe", "adobe.icc"))
    doc.add(svg.Image("swatch.png", 0, 0, 4, 4, color_profile="adobe"))
    doc.save(tmp_path / "page.svg")
    pixel = svg.Document.open(tmp_path / "page.svg").rasterize()[2, 2, :3]
    assert np.allclose(pixel, expected(adobe(), SWATCH), atol=0.02)


def test_image_srgb_profile_ignores_embedded() -> None:
    doc = svg.Document(4, 4)
    doc.add(svg.Image(data_uri(png_with_profile(adobe()), "image/png"), 0, 0, 4, 4, color_profile="sRGB"))
    assert np.allclose(doc.rasterize()[2, 2, :3], np.array(SWATCH) / 255, atol=0.01)


def test_decode_rejects_unknown_keyword() -> None:
    with pytest.raises(ValueError, match="profile"):
        Pixels.decode(png_with_profile(adobe()), profile="cmyk")


def test_without_lcms_fallback_and_one_hint(without_lcms) -> None:
    with pytest.warns(UserWarning, match="color"):
        pixel = icc_page("#ff0000 icc-color(adobe, 0, 1, 0)").rasterize()[2, 2, :3]
    assert np.allclose(pixel, (1, 0, 0), atol=0.01)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        icc_page("#ff0000 icc-color(adobe, 0, 1, 0)").rasterize()


def test_without_lcms_images_decode(without_lcms) -> None:
    decoded = Pixels.decode(png_with_profile(adobe()))
    assert decoded.shape == (4, 4)
