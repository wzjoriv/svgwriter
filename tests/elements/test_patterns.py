import numpy as np
import pytest

import svgwriter as svg


def _dots(**kwargs):
    return svg.Pattern(svg.circle(5, 5, 3, fill="crimson"), width=10, height=10, pattern_units="userSpaceOnUse",
                       **kwargs)


def test_tile_resolves_relative_sizes_and_rejects_missing_box():
    relative = svg.Pattern(width=0.5, height=0.25)
    assert relative.tile(svg.BBox(10, 0, 40, 40)) == (10, 0, 20, 10)
    with pytest.raises(ValueError, match="relative"):
        relative.tile()


def test_to_image_and_back():
    image = _dots().to_image(scale=2)
    assert image.shape == (20, 20) and (image.width, image.height) == (10, 10)
    again = svg.Pattern.from_image(image)
    assert again.tile() == (0, 0, 10, 10)


def test_tiles_cover_the_area():
    assert len(_dots().tiles(svg.BBox(0, 0, 25, 15))) == 6


@pytest.mark.parametrize("transform", [None, "rotate(30)"])
def test_expand_pattern_renders_like_the_fill(transform):
    dots = _dots(pattern_transform=transform) if transform else _dots()
    original = svg.Document(100, 60)
    original.circle(30, 30, 25, fill=dots, stroke="black")
    original.rect(60, 10, 35, 40, fill=dots).rotate(10)
    expanded = svg.Document(100, 60)
    for element in original:
        expanded.add(element.expand_pattern())
    difference = np.abs(original.rasterize(scale=2, background="white") - expanded.rasterize(scale=2, background="white"))
    assert difference[..., :3].mean() < 0.02


def test_expand_pattern_needs_a_pattern_fill():
    with pytest.raises(ValueError, match="pattern"):
        svg.rect(0, 0, 1, 1, fill="red").expand_pattern()


def test_pattern_view_box_scales_its_content_into_each_tile():
    body = ('<defs><pattern id="p" patternUnits="userSpaceOnUse" width="10" height="10" viewBox="0 0 100 100">'
            '<rect width="50" height="100" fill="lime"/></pattern></defs><rect width="10" height="10" fill="url(#p)"/>')
    pixels = svg.ops.rasterize(svg.Document.from_string('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">' + body + "</svg>"))
    assert pixels[5, 2].round(2).tolist() == [0.0, 1.0, 0.0, 1.0]
    assert pixels[5, 8].round(2).tolist() == [0.0, 0.0, 0.0, 0.0]
