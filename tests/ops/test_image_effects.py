import numpy as np
import pytest

import svgwriter as svg


def _render(**attributes):
    doc = svg.Document(60, 60)
    doc.add(svg.Image(np.ones((20, 20, 3)) * [1, 0, 0], 20, 20, 20, 20, **attributes))
    return doc.rasterize(background="white")


def test_plain_image_is_unchanged():
    pixels = _render()
    assert pixels[30, 30].tolist() == pytest.approx([1, 0, 0, 1]) and pixels[5, 5, 1] == pytest.approx(1)


def test_blur_spreads_beyond_the_image_up_to_the_filter_region():
    pixels = _render(filter=svg.Filter(svg.FeGaussianBlur(4)))
    assert pixels[30, 19, 1] < 0.95
    assert pixels[30, 17, 1] == pytest.approx(1)


def test_saturate_zero_turns_gray():
    pixels = _render(filter=svg.Filter(svg.FeColorMatrix(type="saturate", values=0)))
    red, green, blue, _ = pixels[30, 30]
    assert red == pytest.approx(green, abs=0.02) == pytest.approx(blue, abs=0.02)


def test_offset_and_merge_graph():
    shadow = svg.FeOffset(5, 5, in_="SourceAlpha")
    pixels = _render(filter=svg.Filter(svg.FeMerge(shadow, "SourceGraphic")))
    assert pixels[41, 41, :3].sum() < 0.3


def test_mask_keeps_only_the_masked_part():
    mask = svg.Mask(svg.circle(30, 30, 5, fill="white"))
    pixels = _render(mask=mask)
    assert pixels[30, 30].tolist() == pytest.approx([1, 0, 0, 1], abs=0.02)
    assert pixels[21, 21, 1] == pytest.approx(1, abs=0.02)


def test_arithmetic_composite_defaults_to_the_source_graphic():
    pixels = _render(filter=svg.Filter(svg.FeComposite(operator="arithmetic", k2=0.5, k3=0.5)))
    assert pixels[30, 30].tolist() == pytest.approx([1, 0, 0, 1], abs=0.02)
