import numpy as np
import pytest

import svgwriter as svg
from svgwriter.model.elements.structure import Pixels
from svgwriter.ops import composite_rgba, resolve_operator

RED = np.array([1.0, 0, 0, 0.5])
BLUE = np.array([0, 0, 1.0, 1.0])


@pytest.mark.parametrize(
    ("operator", "expected"),
    [
        ("over", [0.5, 0, 0.5, 1]),
        ("in", [1, 0, 0, 0.5]),
        ("out", [0, 0, 0, 0]),
        ("atop", [0.5, 0, 0.5, 1]),
        ("xor", [0, 0, 1, 0.5]),
        ("multiply", [0, 0, 0.5, 1]),
        ("screen", [0.5, 0, 1, 1]),
        ("darken", [0, 0, 0.5, 1]),
        ("lighten", [0.5, 0, 1, 1]),
        ("normal", [0.5, 0, 0.5, 1]),
    ],
)
def test_operators_follow_svg_definitions(operator, expected):
    np.testing.assert_allclose(composite_rgba(RED, BLUE, operator), expected, atol=1e-6)


def test_arithmetic_needs_four_terms_and_adds():
    np.testing.assert_allclose(composite_rgba(RED, BLUE, "arithmetic", k=(0, 1, 1, 0)), [0.5, 0, 1, 1], atol=1e-6)
    with pytest.raises(ValueError, match="k1, k2"):
        composite_rgba(RED, BLUE, "arithmetic")


def test_unknown_operator_lists_choices():
    with pytest.raises(ValueError, match="multiply"):
        resolve_operator("burn")


def test_enum_members_are_accepted():
    assert resolve_operator(svg.CompositeOperator.XOR) is svg.CompositeOperator.XOR
    assert resolve_operator(svg.BlendMode.SCREEN) is svg.BlendMode.SCREEN


def test_broadcast_color_onto_image_and_transparent_stays_zero():
    image = np.zeros((3, 4, 4))
    out = composite_rgba(image, BLUE[None, None], "over")
    assert out.shape == (3, 4, 4)
    np.testing.assert_allclose(out[..., :3], np.broadcast_to(BLUE[:3], (3, 4, 3)))
    assert composite_rgba(image, image).sum() == 0


def test_pixels_operators_and_broadcast():
    glass = Pixels.from_array(np.ones((2, 2, 3)), alpha=0.25)
    under = Pixels.from_array(np.zeros((2, 2, 3)))
    assert (glass | under).rgba()[0, 0].tolist() == pytest.approx([0.25, 0.25, 0.25, 1])
    assert (glass & under).rgba()[0, 0, 3] == pytest.approx(0.25)
    assert (glass - under).rgba()[0, 0, 3] == pytest.approx(0)
    assert (glass ^ under).rgba()[0, 0, 3] == pytest.approx(0.75)
    assert (glass | np.array([[[0, 0, 0, 1.0]]])).shape == (2, 2)


def test_pixels_shape_mismatch_points_to_rasterize():
    with pytest.raises(ValueError, match="rasterize the elements"):
        Pixels.from_array(np.zeros((2, 2))) | Pixels.from_array(np.zeros((3, 3)))


def test_image_pixels_composite_pixel_for_pixel():
    a = svg.Image(np.full((4, 4, 3), 0.5), x=3, y=2)
    b = svg.Image(np.full((4, 4, 3), 0.5), x=3, y=2)
    product = a.pixels * b.pixels
    assert product.shape == (4, 4)
    np.testing.assert_allclose(product.color, 0.25)
    assert a.color[0, 0, 0] == 0.5
    assert a.pixels.composite(b.pixels, "multiply") == product


def test_pixel_operators_match_composite():
    glass = Pixels.from_array(np.ones((2, 2, 3)), alpha=0.5)
    under = Pixels.from_array(np.zeros((2, 2, 3)))
    for result, operator in ((glass | under, "over"), (glass & under, "in"), (glass - under, "out"),
                             (glass ^ under, "xor"), (glass * under, "multiply")):
        assert result == glass.composite(under, operator)
    with pytest.raises(TypeError):
        glass | "red"


def test_images_have_no_compositing_operators():
    a = svg.Image(np.ones((2, 2, 3)))
    b = svg.Image(np.ones((2, 2, 3)))
    assert not hasattr(a, "composite")
    for operation in (lambda: a | b, lambda: a & b, lambda: a ^ b):
        with pytest.raises(TypeError):
            operation()


def test_numbers_and_offsets_keep_transform_meaning():
    image = svg.Image(np.zeros((2, 2)))
    assert str((image * 2).matrix) == "matrix(2 0 0 2 -1 -1)"
    assert str((image - (1, 1)).matrix) == "translate(-1 -1)"


def test_lone_image_rasterizes():
    image = svg.Image(np.ones((3, 3, 3)))
    assert image.rasterize()[..., 3].mean() == pytest.approx(1)
    assert image.to_image().alpha == 1.0


def test_pixels_composite_with_elements_and_documents() -> None:
    import numpy as np

    import svgwriter as svg
    from svgwriter.model.elements.structure import Pixels

    photo = Pixels.from_array(np.full((10, 10, 3), 0.5))
    spot = svg.circle(5, 5, 3, fill="red")
    kept = photo & spot
    assert kept.shape == (10, 10)
    assert kept.rgba()[5, 5, 3] > 0.9 and kept.rgba()[0, 0, 3] == 0
    stamped = photo.on_grid(spot)
    assert stamped.rgba()[5, 5].tolist() == [1.0, 0.0, 0.0, 1.0]
    doc = svg.Document(10, 10)
    doc.rect(0, 0, 5, 10, fill="blue")
    assert ((photo - doc).rgba()[:, :5, 3] == 0).all()
    with pytest.raises(TypeError):
        photo.on_grid("not an element")
