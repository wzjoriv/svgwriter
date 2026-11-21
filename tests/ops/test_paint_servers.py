from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg

LIME = (0.0, 1.0, 0.0, 1.0)
BLUE = (0.0, 0.0, 1.0, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)


def draw(body: str, size: int = 100) -> np.ndarray:
    doc = svg.Document.from_string(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{size}" height="{size}">{body}</svg>')
    return doc.rasterize(background="white")


def test_gradient_inherits_stops_and_geometry_through_its_link() -> None:
    pixels = draw('<linearGradient id="a" x2="0" y2="1"><stop offset="0" stop-color="lime"/>'
                  '<stop offset="1" stop-color="blue"/></linearGradient>'
                  '<linearGradient id="b" xlink:href="#a"/><rect width="100" height="100" fill="url(#b)"/>')
    assert np.allclose(pixels[1, 50], LIME, atol=0.05) and np.allclose(pixels[98, 50], BLUE, atol=0.05)


def test_pattern_inherits_tile_and_content_through_its_link() -> None:
    pixels = draw('<pattern id="a" patternUnits="userSpaceOnUse" width="20" height="20">'
                  '<rect width="10" height="10" fill="lime"/></pattern>'
                  '<pattern id="b" xlink:href="#a"/><rect width="100" height="100" fill="url(#b)"/>')
    assert np.allclose(pixels[25, 25], LIME, atol=0.02) and np.allclose(pixels[35, 35], WHITE, atol=0.02)


def test_stop_color_inherit_and_current_color() -> None:
    pixels = draw('<g stop-color="lime" color="blue"><linearGradient id="g" stop-color="inherit">'
                  '<stop offset="0" stop-color="inherit"/><stop offset="1" stop-color="currentColor"/>'
                  '</linearGradient></g><rect width="100" height="100" fill="url(#g)"/>')
    assert np.allclose(pixels[50, 1], LIME, atol=0.05) and np.allclose(pixels[50, 98], BLUE, atol=0.05)


def test_focal_point_outside_the_circle_moves_onto_it() -> None:
    gradient = ('<radialGradient id="g" cx="0.5" cy="0.5" r="0.25" fx="{fx}" fy="0.5"><stop offset="0" '
                'stop-color="lime"/><stop offset="1" stop-color="blue"/></radialGradient>'
                '<rect width="100" height="100" fill="url(#g)"/>')
    assert np.allclose(draw(gradient.format(fx="0")), draw(gradient.format(fx="0.25")), atol=0.02)


@pytest.mark.parametrize("paint, expected", [("url(#none)", WHITE), ("url(#none) lime", LIME),
                                             ("url(#empty) lime", WHITE), ("url(#tile0) lime", LIME)])
def test_unusable_servers_fall_back(paint: str, expected: tuple) -> None:
    pixels = draw(f'<linearGradient id="empty"/><pattern id="tile0" width="0" height="0"/>'
                  f'<rect width="100" height="100" fill="{paint}"/>')
    assert np.allclose(pixels[50, 50], expected, atol=0.02)


def test_bounding_box_paint_on_a_flat_shape_uses_the_fallback() -> None:
    pixels = draw('<linearGradient id="g"><stop offset="0" stop-color="blue"/></linearGradient>'
                  '<line x1="0" y1="50" x2="100" y2="50" stroke="url(#g) lime" stroke-width="10"/>')
    assert np.allclose(pixels[50, 50], LIME, atol=0.02)


def test_line_fill_is_not_painted() -> None:
    pixels = draw('<line x1="0" y1="50" x2="100" y2="50" fill="black" stroke="none" stroke-width="10"/>')
    assert np.allclose(pixels[50, 50], WHITE, atol=0.02)


@pytest.mark.parametrize("pattern", [
    '<pattern id="p" patternUnits="userSpaceOnUse" x="10" y="10" width="20" height="20">'
    '<rect x="5" y="5" width="10" height="10" fill="lime"/></pattern>',
    '<pattern id="p" width="0.2" height="0.2"><rect x="5" y="5" width="10" height="10" fill="lime"/></pattern>',
    '<pattern id="p" width="0.2" height="0.2" patternContentUnits="objectBoundingBox">'
    '<rect x=".05" y=".05" width=".1" height=".1" fill="lime"/></pattern>',
])
def test_pattern_tiles_land_where_the_units_say(pattern: str) -> None:
    pixels = draw(pattern + '<rect x="10" y="10" width="100" height="100" fill="url(#p)"/>', size=120)
    assert np.allclose(pixels[20, 20], LIME, atol=0.02) and np.allclose(pixels[60, 60], LIME, atol=0.02)
    assert np.allclose(pixels[28, 28], WHITE, atol=0.02)


@pytest.mark.parametrize("space, middle", [("sRGB", 0.5), ("linearRGB", 0.735)])
def test_gradient_blends_in_its_color_interpolation_space(space: str, middle: float) -> None:
    pixels = draw(f'<linearGradient id="g" color-interpolation="{space}"><stop offset="0" stop-color="black"/>'
                  '<stop offset="1" stop-color="white"/></linearGradient><rect width="100" height="100" fill="url(#g)"/>')
    assert pixels[50, 50, 0] == pytest.approx(middle, abs=0.03)


def test_gradient_strokes_a_line_across_its_bounding_box() -> None:
    pixels = draw('<linearGradient id="g"><stop offset="0" stop-color="lime"/><stop offset="1" stop-color="blue"/>'
                  '</linearGradient><line x1="90" y1="10" x2="10" y2="90" stroke="url(#g)" stroke-width="10"/>')
    assert np.allclose(pixels[88, 12], LIME, atol=0.1) and np.allclose(pixels[12, 88], BLUE, atol=0.1)
