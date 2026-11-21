from __future__ import annotations

import io
import re
import sys

import numpy as np
import pytest

import svgwriter as svg
from svgwriter._internal._icc_embedded import embed_profile, embedded_profile
from svgwriter._internal._icc_output import output_profile
from svgwriter.export import find_importer

lcms2 = pytest.importorskip("lcms2")
Image = pytest.importorskip("PIL.Image")

P3_RED = [234, 51, 35]


PAPER_TINT = 16
"""At most about 6% ink on white: python-lcms2 0.3 profiles generated from a CMYK space tint paper slightly."""


@pytest.fixture(scope="module")
def cmyk_profile() -> bytes:
    from lcms2 import Profile, spaces

    return Profile.from_space(spaces.cmyk).to_bytes()


def red() -> svg.Document:
    doc = svg.Document(8, 4)
    doc.rect(0, 0, 8, 4, fill="red")
    return doc


def opened(data: bytes):
    return Image.open(io.BytesIO(data))


def description(data: bytes) -> str:
    return lcms2.Profile.from_bytes(opened(data).info["icc_profile"]).description


@pytest.mark.parametrize("name", ["png", "jpeg", "tiff"])
def test_srgb_tags_the_pixels_without_changing_them(name):
    tagged, plain = red().export(name, icc="srgb"), red().export(name)
    assert description(tagged) == "sRGB built-in"
    assert np.array_equal(np.asarray(opened(tagged)), np.asarray(opened(plain)))


@pytest.mark.parametrize("name", ["png", "jpeg", "tiff"])
def test_display_p3_converts_the_pixels_and_embeds_the_profile(name):
    data = red().export(name, icc="display-p3")
    assert description(data) == "Display P3"
    assert np.asarray(opened(data))[0, 0, :3].tolist() == pytest.approx(P3_RED, abs=2)


def test_a_p3_png_reads_back_as_the_same_srgb_color():
    doc = find_importer(".png").function(red().export("png", icc="display-p3"))
    pixels = np.asarray(doc[0].pixels.rgba())
    assert pixels[0, 0, :3] * 255 == pytest.approx([255, 0, 0], abs=3)


def test_profile_bytes_are_embedded_as_given():
    profile = output_profile("display-p3").data
    assert embedded_profile(red().export("png", icc=profile)) == profile


def test_png_replaces_its_colour_chunks_with_one_iccp_chunk():
    data = embed_profile(embed_profile(red().export("png"), b"first"), b"second")
    assert data.count(b"iCCP") == 1 and embedded_profile(data) == b"second"


def test_a_large_profile_spans_several_jpeg_segments():
    profile = bytes(range(256)) * 600
    data = embed_profile(red().export("jpeg"), profile)
    assert data.count(b"ICC_PROFILE") == 3
    assert embedded_profile(data) == profile
    assert opened(data).size == (8, 4)


def test_an_animated_png_carries_the_profile_and_converted_frames():
    doc = svg.Document(20, 10)
    ball = doc.circle(5, 5, 4, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=5, to=15, dur=1))
    data = doc.export("png", animate=True, fps=4, icc="display-p3")
    assert b"acTL" in data and data.count(b"iCCP") == 1
    assert np.asarray(opened(data).convert("RGBA"))[5, 5, :3].tolist() == pytest.approx(P3_RED, abs=2)


def test_cmyk_tiff_writes_ink_on_a_white_page(cmyk_profile):
    image = opened(red().export("tiff", icc=cmyk_profile, dpi=300))
    assert image.mode == "CMYK" and image.info["dpi"] == pytest.approx((300, 300))
    cyan, magenta, yellow, _ = np.asarray(image)[0, 0].tolist()
    assert cyan < 20 and magenta > 200 and yellow > 200
    blank = np.asarray(opened(svg.Document(4, 4).export("tiff", icc=cmyk_profile)))
    assert blank.max() <= PAPER_TINT


def test_tiff_keeps_alpha_and_resolution_without_a_profile():
    image = opened(svg.Document(6, 3).export("tiff", scale=2))
    assert image.mode == "RGBA" and image.size == (12, 6) and image.info["dpi"] == pytest.approx((192, 192))
    assert "icc_profile" not in image.info


def test_raster_formats_refuse_what_they_cannot_hold(cmyk_profile):
    with pytest.raises(ValueError, match="webp cannot embed an ICC profile"):
        red().export("webp", icc="srgb")
    with pytest.raises(ValueError, match="RGB profiles, not CMYK"):
        red().export("png", icc=cmyk_profile)
    with pytest.raises(ValueError, match="unknown ICC profile 'adobe'"):
        red().export("png", icc="adobe")
    with pytest.raises(ValueError, match="not a readable ICC profile"):
        red().export("png", icc=b"nonsense")


def _check_xref(data: bytes) -> None:
    for section in re.finditer(rb"xref\n((?:\d+ \d+\n(?:\d{10} \d{5} [nf] ?\n)+)+)", data):
        for start, _, entries in re.findall(rb"(\d+) (\d+)\n((?:\d{10} \d{5} [nf] ?\n)+)", section.group(1)):
            for index, (offset, kind) in enumerate(re.findall(rb"(\d{10}) \d{5} ([nf])", entries)):
                if kind == b"n":
                    assert re.match(rb"%d 0 obj" % (int(start) + index), data[int(offset):])
    previous = re.findall(rb"/Prev (\d+)", data)
    assert all(data[int(offset):].startswith(b"xref") for offset in previous)


def test_pdf_srgb_output_intent_is_an_incremental_update():
    plain, tagged = red().export("pdf"), red().export("pdf", icc="srgb")
    assert tagged.startswith(plain)
    assert b"/S /GTS_PDFA1" in tagged and b"/OutputIntents [" in tagged and b"/N 3" in tagged
    _check_xref(tagged)
    assert find_importer("pdf").function(tagged)[0].get("fill") == "#ff0000"


def test_pdf_cmyk_output_intent_names_the_print_condition(cmyk_profile):
    data = svg.export.export([red(), red()], "pdf", icc=cmyk_profile)
    assert b"/S /GTS_PDFX" in data and b"/N 4" in data and data.count(b"/Type /Page\n") == 2
    _check_xref(data)


def test_pdf_refuses_rgb_profiles_other_than_srgb():
    with pytest.raises(ValueError, match="'srgb' or a CMYK profile"):
        red().export("pdf", icc="display-p3")


def test_profiles_are_parsed_once():
    assert output_profile("display-p3") is output_profile("display-p3")


def test_without_lcms2_the_error_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "lcms2", None)
    output_profile.cache_clear()
    try:
        with pytest.raises(ImportError, match=r"pysvgwriter\[color\]"):
            red().export("png", icc="srgb")
    finally:
        output_profile.cache_clear()
