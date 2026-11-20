"""
BMP, GIF and PPM/PGM writers and the PNM reader.
"""

from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.elements.structure import Image, Pixels
from svgwriter.export._raster._encoders import decode_pnm, encode_bmp, encode_gif, encode_pnm


def _noise(rows: int = 40, columns: int = 50, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, 256, (rows, columns, 4), dtype=np.uint8)


def _decode(data: bytes) -> np.ndarray:
    pixels = Pixels.decode(data)
    return np.rint(pixels.rgba() * 255).astype(np.uint8)


def _doc() -> svg.Document:
    doc = svg.Document(16, 8)
    doc.rect(0, 0, 8, 8, fill="red")
    doc.circle(12, 4, 3, fill="blue")
    return doc


def test_bmp_round_trip_keeps_alpha() -> None:
    rgba = _noise()
    rgba[..., 3] = np.linspace(0, 255, rgba.shape[1], dtype=np.uint8)[None, :]
    rgba[..., 3][:, 0] = 255
    out = _decode(encode_bmp(rgba))
    assert out.shape == rgba.shape
    assert np.array_equal(out[..., 3], rgba[..., 3])
    opaque = rgba[..., 3] == 255
    assert np.array_equal(out[opaque][:, :3], rgba[opaque][:, :3])


def test_bmp_scalar_alpha_matches_full_alpha_array() -> None:
    color = _noise()[..., :3]
    full = np.dstack([color, np.full(color.shape[:2], 255, np.uint8)])
    broadcast = np.concatenate([color, np.broadcast_to(np.uint8(255), color.shape[:2] + (1,))], axis=2)
    assert encode_bmp(full) == encode_bmp(broadcast)


def test_bmp_fully_transparent() -> None:
    out = _decode(encode_bmp(np.zeros((3, 4, 4), np.uint8)))
    assert out.shape == (3, 4, 4)
    assert (out[..., 3] == 0).all()


def test_bmp_rejects_bad_array() -> None:
    with pytest.raises(ValueError):
        encode_bmp(np.zeros((2, 2, 3), np.uint8))


def test_gif_exact_palette_round_trip() -> None:
    rng = np.random.default_rng(1)
    palette = rng.integers(0, 256, (37, 3), dtype=np.uint8)
    picks = rng.integers(0, 37, (30, 45))
    rgba = np.dstack([palette[picks], np.full((30, 45), 255, np.uint8)])
    assert np.array_equal(_decode(encode_gif(rgba)), rgba)


def test_gif_large_image_forces_lzw_table_resets() -> None:
    rng = np.random.default_rng(2)
    picks = rng.integers(0, 256, (120, 160))
    palette = rng.integers(0, 256, (256, 3), dtype=np.uint8)
    rgba = np.dstack([palette[picks], np.full(picks.shape, 255, np.uint8)])
    assert np.array_equal(_decode(encode_gif(rgba))[..., :3], rgba[..., :3])


@pytest.mark.parametrize("colors", [1, 2, 3, 4, 5, 16, 17, 255, 256])
def test_gif_palette_sizes(colors: int) -> None:
    rng = np.random.default_rng(colors)
    palette = rng.integers(0, 256, (colors, 3), dtype=np.uint8)
    picks = np.arange(24 * 24).reshape(24, 24) % colors
    rgba = np.dstack([palette[picks], np.full(picks.shape, 255, np.uint8)])
    assert np.array_equal(_decode(encode_gif(rgba)), rgba)


def test_gif_quantizes_to_at_most_256_colors() -> None:
    out = _decode(encode_gif(_noise(64, 64, seed=3) | np.array([0, 0, 0, 255], np.uint8)))
    assert len(np.unique(out[..., :3].reshape(-1, 3), axis=0)) <= 256


def test_gif_quantization_is_close_on_smooth_gradient() -> None:
    ramp = np.linspace(0, 255, 64, dtype=np.uint8)
    rgba = np.dstack([np.tile(ramp, (64, 1)), np.tile(ramp[::-1], (64, 1)), np.tile(ramp[:, None], (1, 64)),
                      np.full((64, 64), 255, np.uint8)])
    out = _decode(encode_gif(rgba)).astype(int)
    assert np.abs(out[..., :3] - rgba[..., :3]).mean() < 8


def test_gif_is_deterministic() -> None:
    rgba = _noise(50, 50, seed=4)
    assert encode_gif(rgba) == encode_gif(rgba.copy())


def test_gif_transparency_survives() -> None:
    rgba = _noise(10, 12, seed=5)
    rgba[..., 3] = np.where(np.arange(12) % 2, 255, 0).astype(np.uint8)[None, :]
    out = _decode(encode_gif(rgba))
    assert np.array_equal(out[..., 3] == 0, rgba[..., 3] == 0)
    assert (out[..., 3][rgba[..., 3] == 255] == 255).all()


def test_gif_alpha_threshold_is_half() -> None:
    rgba = np.zeros((1, 2, 4), np.uint8)
    rgba[0, 0] = (10, 20, 30, 127)
    rgba[0, 1] = (10, 20, 30, 128)
    out = _decode(encode_gif(rgba))
    assert out[0, 0, 3] == 0 and out[0, 1, 3] == 255


def test_gif_fully_transparent() -> None:
    out = _decode(encode_gif(np.zeros((3, 3, 4), np.uint8)))
    assert (out[..., 3] == 0).all()


def test_pnm_color_round_trip_composites_on_white() -> None:
    rgba = np.array([[[255, 0, 0, 255], [0, 0, 255, 0]]], np.uint8)
    data = encode_pnm(rgba, gray=False)
    assert data.startswith(b"P6\n2 1\n255\n")
    assert decode_pnm(data).tolist() == [[[255, 0, 0], [255, 255, 255]]]


def test_pnm_background_option() -> None:
    rgba = np.zeros((1, 1, 4), np.uint8)
    assert decode_pnm(encode_pnm(rgba, gray=False, background=(1, 2, 3))).tolist() == [[[1, 2, 3]]]


def test_pnm_auto_gray_and_forced_modes() -> None:
    gray = np.dstack([np.full((2, 2, 3), 77, np.uint8), np.full((2, 2), 255, np.uint8)])
    assert encode_pnm(gray).startswith(b"P5")
    assert decode_pnm(encode_pnm(gray)).tolist() == [[77, 77], [77, 77]]
    assert encode_pnm(gray, gray=False).startswith(b"P6")
    colored = gray.copy()
    colored[0, 0, 0] = 0
    assert encode_pnm(colored).startswith(b"P6")
    forced = decode_pnm(encode_pnm(colored, gray=True))
    assert forced.shape == (2, 2)
    assert forced[0, 0] == round(77 * 0.587 + 77 * 0.114)


def test_pnm_fully_transparent_is_white() -> None:
    data = encode_pnm(np.zeros((2, 2, 4), np.uint8))
    assert data.startswith(b"P5")
    assert (decode_pnm(data) == 255).all()


def test_pnm_scalar_alpha_matches_full_alpha_array() -> None:
    color = _noise()[..., :3]
    full = np.dstack([color, np.full(color.shape[:2], 255, np.uint8)])
    assert np.array_equal(decode_pnm(encode_pnm(full, gray=False)), color)


def test_decode_ascii_p1() -> None:
    assert decode_pnm(b"P1\n# comment\n3 2\n1 0 1\n0 1 0\n").tolist() == [[0, 255, 0], [255, 0, 255]]
    assert decode_pnm(b"P1 3 1 101").tolist() == [[0, 255, 0]]


def test_decode_ascii_p2() -> None:
    out = decode_pnm(b"P2\n2 2\n255\n0 64\n128 255\n")
    assert out.dtype == np.uint8 and out.tolist() == [[0, 64], [128, 255]]
    scaled = decode_pnm(b"P2 2 1 10 0 5")
    assert scaled.dtype == np.float32 and scaled.tolist() == [[0.0, 0.5]]


def test_decode_ascii_p3() -> None:
    out = decode_pnm(b"P3\n2 1\n255\n255 0 0  # red\n0 0 255\n")
    assert out.tolist() == [[[255, 0, 0], [0, 0, 255]]]


def test_decode_binary_p4() -> None:
    assert decode_pnm(b"P4\n3 2\n" + bytes([0b10100000, 0b01000000])).tolist() == [[0, 255, 0], [255, 0, 255]]


def test_decode_binary_p5_with_comment() -> None:
    assert decode_pnm(b"P5\n# c\n2 1\n255\n" + bytes([3, 4])).tolist() == [[3, 4]]


def test_decode_16_bit_p6() -> None:
    data = b"P6\n2 1\n65535\n" + np.array([65535, 0, 32768, 0, 65535, 0], ">u2").tobytes()
    out = decode_pnm(data)
    assert out.shape == (1, 2, 3) and out.dtype == np.float32
    assert out[0, 0].tolist() == [1.0, 0.0, pytest.approx(32768 / 65535)]
    assert Pixels.from_array(out).shape == (1, 2)


@pytest.mark.parametrize("data", [b"", b"P7\n1 1\n255\n", b"P6\n1 1\n255\n\x00", b"P2\n1 1\n255\n", b"P5\n0 1\n255\n",
                                  b"P5\n1 1\n70000\n", b"P2\n1 1\n10\n11\n", b"P5\n1"])
def test_decode_rejects_bad_data(data: bytes) -> None:
    with pytest.raises(ValueError):
        decode_pnm(data)


def test_pixels_decode_routes_pnm() -> None:
    pixels = Pixels.decode(b"P3\n1 1\n255\n255 0 0\n")
    assert pixels.rgba().tolist() == [[[1.0, 0.0, 0.0, 1.0]]]


@pytest.mark.parametrize("format", ["bmp", "gif", "ppm"])
def test_pixels_and_image_encode_tables(format: str) -> None:
    pixels = Pixels.from_array(np.zeros((2, 3, 3)))
    data = pixels.encode(format)
    assert data == Image(np.zeros((2, 3, 3))).encode(format.upper())
    assert Pixels.decode(data).shape == (2, 3)


def test_encode_unknown_format_still_raises() -> None:
    with pytest.raises(ValueError):
        Pixels.from_array(np.zeros((1, 1, 3))).encode("tiff")


@pytest.mark.parametrize(("name", "magic"), [("a.bmp", b"BM"), ("a.gif", b"GIF89a"), ("a.ppm", b"P6"),
                                             ("a.pnm", b"P6")])
def test_save_and_load_route_by_extension(tmp_path, name: str, magic: bytes) -> None:
    path = tmp_path / name
    svg.export.save(_doc(), path)
    assert path.read_bytes().startswith(magic)
    loaded = svg.export.load(path)
    assert loaded.root.view_box.width == 16 and len(loaded) == 1


def test_save_pgm_and_load(tmp_path) -> None:
    doc = svg.Document(4, 4)
    doc.rect(0, 0, 4, 4, fill="gray")
    path = tmp_path / "g.pgm"
    svg.export.save(doc, path, background="white")
    assert path.read_bytes().startswith(b"P5")
    assert len(svg.export.load(path)) == 1


def test_exporters_accept_png_options() -> None:
    for name in ("bmp", "gif", "ppm"):
        data = svg.export.export(_doc(), name, scale=2, padding=1, background="white", quality=50)
        assert Pixels.decode(data).shape == (20, 36)
    assert Pixels.decode(svg.export.export(_doc(), "gif", size=10)).shape == (10, 10)


def test_gif_exporter_keeps_transparent_background() -> None:
    out = _decode(svg.export.export(_doc(), "gif"))
    assert out[0, 15, 3] == 0 and out[4, 2, 3] == 255


def test_animated_documents_export_animated_gifs():
    import svgwriter as svg
    from svgwriter.elements.structure import Pixels

    doc = svg.Document(40, 20)
    ball = doc.circle(4, 10, 4, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=4, to=36, dur=1))
    animated = svg.export.export(doc, "gif", fps=5)
    assert animated.count(b"NETSCAPE2.0") == 1 and animated.count(bytes([0x2C, 0, 0, 0, 0])) == 5
    still = svg.export.export(doc, "gif", animate=False)
    assert b"NETSCAPE2.0" not in still and Pixels.decode(animated).shape == (20, 40)


def test_time_option_picks_the_frame_for_still_formats():
    import numpy as np

    import svgwriter as svg
    from svgwriter.elements.structure import Pixels

    doc = svg.Document(40, 20)
    ball = doc.circle(5, 10, 4, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=5, to=35, dur=1, fill="freeze"))
    start = Pixels.decode(svg.export.export(doc, "png")).rgba()
    end = Pixels.decode(svg.export.export(doc, "png", time=1)).rgba()
    assert np.argmax(start[10, :, 3]) < 10 < 30 < np.argmax(end[10, :, 3]) + 5


def test_animated_png_and_webp_on_request():
    import skia

    import svgwriter as svg

    doc = svg.Document(40, 20)
    ball = doc.circle(4, 10, 4, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=4, to=36, dur=1))
    apng = svg.export.export(doc, "png", animate=True, fps=4)
    assert apng.count(b"fcTL") == 4 and apng.count(b"acTL") == 1
    webp = svg.export.export(doc, "webp", animate=True, fps=4)
    assert skia.Codec.MakeFromData(skia.Data.MakeWithCopy(webp)).getFrameCount() == 4
    assert b"acTL" not in svg.export.export(doc, "png")
