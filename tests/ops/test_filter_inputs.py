from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg

LIME = (0.0, 1.0, 0.0, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)
SHIFT = ('<filter id="f" filterUnits="userSpaceOnUse" x="0" y="0" width="100" height="100">'
         '<feOffset in="{source}" dx="50"/></filter>')


def draw(body: str) -> np.ndarray:
    doc = svg.Document.from_string(f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">{body}</svg>')
    return doc.rasterize(background="white")


def test_background_image_is_what_the_enabling_group_painted_before() -> None:
    pixels = draw(SHIFT.format(source="BackgroundImage") + '<g enable-background="new">'
                  '<rect width="40" height="40" fill="lime"/><g filter="url(#f)"/>'
                  '<rect y="60" width="10" height="10" fill="red"/></g>')
    assert np.allclose(pixels[20, 70], LIME, atol=0.02) and np.allclose(pixels[65, 55], WHITE, atol=0.02)


def test_background_image_is_empty_without_an_enabling_ancestor() -> None:
    pixels = draw(SHIFT.format(source="BackgroundImage") + '<rect width="40" height="40" fill="lime"/>'
                  '<g filter="url(#f)"/>')
    assert np.allclose(pixels[20, 70], WHITE, atol=0.02)


def test_background_alpha_keeps_only_coverage() -> None:
    pixels = draw(SHIFT.format(source="BackgroundAlpha") + '<g enable-background="new">'
                  '<rect width="40" height="40" fill="lime"/><g filter="url(#f)"/></g>')
    assert np.allclose(pixels[20, 70], (0, 0, 0, 1), atol=0.02)


@pytest.mark.parametrize("source, paint", [("FillPaint", 'fill="lime"'),
                                           ("StrokePaint", 'fill="red" stroke="lime"')])
def test_paint_inputs_flood_the_region_with_the_element_paint(source: str, paint: str) -> None:
    pixels = draw(f'<filter id="f" x="0" y="0" width="1" height="1"><feMerge><feMergeNode in="{source}"/>'
                  f'</feMerge></filter><circle cx="50" cy="50" r="40" {paint} filter="url(#f)"/>')
    assert np.allclose(pixels[12, 12], LIME, atol=0.02)


def test_group_opacity_fades_a_filter_result_inside_it() -> None:
    pixels = draw('<filter id="f" primitiveUnits="objectBoundingBox" x="0" y="0" width="1" height="1">'
                  '<feFlood flood-color="black"/></filter><g opacity="0.5"><rect width="100" height="100" filter="url(#f)"/></g>')
    assert pixels[50, 50, 0] == pytest.approx(0.5, abs=0.02)
