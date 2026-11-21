from __future__ import annotations

import base64

import numpy as np
import pytest

import svgwriter as svg

LIME = (0.0, 1.0, 0.0, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)
RED = (1.0, 0.0, 0.0, 1.0)


def draw(body: str) -> np.ndarray:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100" '
        f'height="100">{body}</svg>')
    return doc.rasterize(background="white")


def png_uri(color: tuple[float, float, float]) -> str:
    data = svg.Image(np.tile(color, (4, 4, 1))).encode("png")
    return "data:image/png;base64," + base64.b64encode(data).decode()


def test_fe_image_draws_a_referenced_element_in_user_space() -> None:
    pixels = draw('<defs><rect id="r" width="50" height="50" fill="lime"/></defs>'
                  '<filter id="f" x="0" y="0" width="1" height="1"><feImage xlink:href="#r"/></filter>'
                  '<rect width="100" height="100" fill="red" filter="url(#f)"/>')
    assert np.allclose(pixels[25, 25], LIME, atol=0.02) and np.allclose(pixels[75, 75], WHITE, atol=0.02)


def test_fe_image_draws_embedded_pixels_into_its_subregion() -> None:
    pixels = draw(f'<filter id="f" filterUnits="userSpaceOnUse" x="0" y="0" width="100" height="100">'
                  f'<feImage x="50" y="0" width="50" height="50" xlink:href="{png_uri((0, 1, 0))}"/></filter>'
                  '<rect width="100" height="100" fill="red" filter="url(#f)"/>')
    assert np.allclose(pixels[25, 75], LIME, atol=0.02) and np.allclose(pixels[25, 25], WHITE, atol=0.02)


def test_fe_tile_repeats_its_input_subregion() -> None:
    pixels = draw('<filter id="f" filterUnits="userSpaceOnUse" primitiveUnits="userSpaceOnUse" x="0" y="0" '
                  'width="100" height="100"><feFlood x="0" y="0" width="10" height="10" flood-color="lime"/>'
                  '<feOffset x="0" y="0" width="20" height="20"/><feTile/></filter>'
                  '<g filter="url(#f)"/>')
    assert np.allclose(pixels[45, 45], LIME, atol=0.02) and np.allclose(pixels[55, 55], WHITE, atol=0.02)


@pytest.mark.parametrize("operator, inside, outside", [("in", LIME, WHITE), ("out", WHITE, LIME)])
def test_fe_composite_combines_fe_image_inputs(operator: str, inside: tuple, outside: tuple) -> None:
    pixels = draw('<defs><rect id="a" width="100" height="100" fill="lime"/><rect id="b" width="50" '
                  'height="100" fill="blue"/></defs><filter id="f" x="0" y="0" width="1" height="1">'
                  '<feImage xlink:href="#b" result="b"/><feImage xlink:href="#a" result="a"/>'
                  f'<feComposite in="a" in2="b" operator="{operator}"/></filter>'
                  '<rect width="100" height="100" filter="url(#f)"/>')
    assert np.allclose(pixels[50, 25], inside, atol=0.02) and np.allclose(pixels[50, 75], outside, atol=0.02)


def test_filtered_image_is_the_source_graphic() -> None:
    pixels = draw(f'<filter id="f" x="0" y="0" width="1" height="1"><feImage xlink:href="{png_uri((0, 0, 1))}"'
                  ' result="i"/><feComposite in="SourceGraphic" in2="i" operator="over"/></filter>'
                  f'<image width="100" height="100" xlink:href="{png_uri((1, 0, 0))}" filter="url(#f)"/>')
    assert np.allclose(pixels[50, 50], RED, atol=0.02)


@pytest.mark.parametrize("definition, reference", [("", "url(#missing)"), ('<filter id="f"/>', "url(#f)"),
                                                   ('<rect id="f"/>', "url(#f)")])
def test_element_with_an_unusable_filter_is_not_drawn(definition: str, reference: str) -> None:
    pixels = draw(f'<defs>{definition}</defs><rect width="100" height="100" fill="red" filter="{reference}"/>')
    assert np.allclose(pixels[50, 50], WHITE, atol=0.02)


def test_fe_convolve_matrix_runs_on_a_group_and_applies_its_bias() -> None:
    body = ('<filter id="f" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">'
            '<feConvolveMatrix kernelMatrix="0 0 0 0 1 0 0 0 0" bias="{bias}"/></filter>'
            '<g filter="url(#f)"><rect width="100" height="100" fill="black"/></g>')
    assert np.allclose(draw(body.format(bias=0))[50, 50], (0, 0, 0, 1), atol=0.02)
    assert np.allclose(draw(body.format(bias=0.5))[50, 50], (0.5, 0.5, 0.5, 1), atol=0.02)


def test_filtered_image_runs_through_the_engine() -> None:
    pixels = draw('<filter id="f" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">'
                  '<feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 1  0 0 0 0 0  0 0 0 1 0"/></filter>'
                  f'<image width="100" height="100" xlink:href="{png_uri((1, 0, 0))}" filter="url(#f)"/>')
    assert np.allclose(pixels[50, 50], LIME, atol=0.02)


@pytest.mark.parametrize("primitive, lime, white", [
    ('<feOffset dx="0.25" dy="0.25"/>', (65, 65), (25, 25)),
    ('<feMorphology operator="dilate" radius="0.25"/>', (15, 15), (5, 5)),
    ('<feGaussianBlur stdDeviation="0.25"/>', (40, 68), (40, 97)),
])
def test_bounding_box_primitive_units_scale_primitive_lengths(primitive: str, lime: tuple[int, int],
                                                              white: tuple[int, int]) -> None:
    pixels = draw('<filter id="f" primitiveUnits="objectBoundingBox" x="-1" y="-1" width="3" height="3">'
                  f'{primitive}</filter><rect x="20" y="20" width="40" height="40" fill="lime" filter="url(#f)"/>')
    assert pixels[lime][0] < 0.9 and np.allclose(pixels[white], WHITE, atol=0.02)


def test_fe_image_fits_its_unclipped_subregion() -> None:
    pixels = draw(f'<filter id="f" x="0" y="0" width="1" height="1"><feImage width="100" '
                  f'xlink:href="{png_uri((0, 1, 0))}"/></filter>'
                  '<rect width="50" height="50" fill="red" filter="url(#f)"/>')
    assert np.allclose(pixels[25, 10], WHITE, atol=0.02) and np.allclose(pixels[25, 40], LIME, atol=0.02)


@pytest.mark.parametrize("space, moved", [("linearRGB", False), ("sRGB", True)])
def test_fe_displacement_map_reads_its_map_in_the_interpolation_space(space: str, moved: bool) -> None:
    half_in_linear_light = 0.7354
    pixels = draw(f'<defs><rect id="t" x="40" y="40" width="20" height="20" fill="lime"/></defs>'
                  f'<filter id="f" x="0" y="0" width="1" height="1" color-interpolation-filters="{space}">'
                  f'<feImage result="m" xlink:href="{png_uri((half_in_linear_light,) * 3)}"/>'
                  '<feImage xlink:href="#t" result="t"/><feDisplacementMap in="t" in2="m" scale="40" '
                  'xChannelSelector="R" yChannelSelector="G"/></filter><rect width="100" height="100" filter="url(#f)"/>')
    assert np.allclose(pixels[57, 57], WHITE if moved else LIME, atol=0.05)


def test_fe_convolve_matrix_bias_lifts_only_painted_pixels() -> None:
    doc = svg.Document.from_string(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><filter id="f" filterUnits="userSpaceOnUse" '
        'x="0" y="0" width="100" height="100"><feConvolveMatrix kernelMatrix="0 0 0 0 1 0 0 0 0" bias="1"/></filter>'
        '<g filter="url(#f)"><rect width="50" height="100" fill="black"/></g></svg>')
    pixels = doc.rasterize()
    assert np.allclose(pixels[50, 25], WHITE, atol=0.02) and pixels[50, 75, 3] == pytest.approx(0.0)


def test_filters_built_in_python_read_their_enum_keywords() -> None:
    doc = svg.Document(100, 100)
    doc.define(svg.rect(0, 0, 100, 100, fill="lime", id="r"))
    image = svg.FeImage("#r")
    clip = svg.FeComposite(svg.CompositeOperator.IN, in_=image, in2=svg.StandardInput.SOURCE_ALPHA)
    effect = doc.define(svg.Filter(image, clip, x=0, y=0, width=1, height=1))
    doc.circle(50, 50, 20, fill="red", filter=effect)
    pixels = doc.rasterize(background="white")
    assert np.allclose(pixels[50, 50], LIME, atol=0.02) and np.allclose(pixels[5, 5], WHITE, atol=0.02)
