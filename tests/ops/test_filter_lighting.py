from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg

LIGHT_UP = ('<filter id="f"><feDiffuseLighting surfaceScale="10" lighting-color="{color}">'
            '<feDistantLight elevation="90"/></feDiffuseLighting></filter>')


def draw(body: str) -> np.ndarray:
    doc = svg.Document.from_string(f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60">{body}</svg>')
    return doc.rasterize(background="white")


def test_diffuse_light_darkens_the_rim_of_a_shape() -> None:
    pixels = draw(LIGHT_UP.format(color="lime") + '<circle cx="30" cy="30" r="15" fill="red" filter="url(#f)"/>')
    rim = pixels[30, 13:19, 1].min()
    assert pixels[30, 30, 1] == pytest.approx(1.0, abs=0.02) and rim < 0.5


def test_a_later_sibling_keeps_the_lit_rim() -> None:
    pixels = draw(LIGHT_UP.format(color="lime") + '<g><circle cx="30" cy="30" r="15" fill="red" filter="url(#f)"/>'
                  '<circle cx="80" cy="30" r="10" fill="red"/></g>')
    assert pixels[30, 13:19, 1].min() < 0.5 and np.allclose(pixels[30, 80], (1, 0, 0, 1), atol=0.02)


def test_lighting_color_survives_the_linear_light_round_trip() -> None:
    pixels = draw(LIGHT_UP.format(color="#808080") + '<rect width="100" height="60" filter="url(#f)"/>')
    assert pixels[30, 50, 0] == pytest.approx(128 / 255, abs=0.02)


def test_point_light_is_placed_in_user_space() -> None:
    pixels = draw('<filter id="f" x="0" y="0" width="1" height="1"><feDiffuseLighting lighting-color="white">'
                  '<fePointLight x="10" y="30" z="10"/></feDiffuseLighting></filter>'
                  '<rect width="100" height="60" filter="url(#f)"/>')
    assert pixels[30, 10, 0] > pixels[30, 90, 0] + 0.3
