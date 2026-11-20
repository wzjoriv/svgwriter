import pytest

import svgwriter as svg

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100" height="100">'


def _pixel(body: str, *points: tuple[int, int]) -> list[list[float]]:
    pixels = svg.ops.rasterize(svg.Document.from_string(HEAD + body + "</svg>"))
    return [pixels[y, x].round(2).tolist() for x, y in points]


@pytest.mark.parametrize(("overflow", "outside"), [("hidden", [0.0, 0.0, 0.0, 0.0]), ("visible", [1.0, 0.0, 0.0, 1.0])])
def test_symbol_is_fitted_and_clipped_to_the_use_viewport(overflow, outside):
    body = (f'<symbol id="s" viewBox="0 0 10 10" preserveAspectRatio="none" overflow="{overflow}">'
            '<rect width="5" height="5" fill="blue"/><rect y="5" width="40" height="5" fill="red"/></symbol>'
            '<use xlink:href="#s" width="50" height="100"/>')
    inside, beyond = _pixel(body, (10, 10), (70, 70))
    assert inside == [0.0, 0.0, 1.0, 1.0]
    assert beyond == outside


def test_instance_inherits_from_the_use_and_is_offset():
    body = '<defs><rect id="r" width="10" height="10"/></defs><use xlink:href="#r" x="20" y="20" fill="lime"/>'
    assert _pixel(body, (25, 25), (5, 5)) == [[0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0]]


def test_cyclic_uses_are_not_rendered():
    body = ('<use id="a" xlink:href="#b" fill="red"/><use id="b" xlink:href="#a"/>'
            '<g id="g"><rect width="10" height="10"/><use xlink:href="#g"/></g>')
    assert _pixel(body, (5, 5), (50, 50)) == [[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0]]


def test_use_of_an_element_in_another_file(tmp_path):
    (tmp_path / "shapes.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect id="box" width="10" '
                                         'height="10" fill="blue"/></svg>', encoding="utf-8")
    page = tmp_path / "page.svg"
    page.write_text(HEAD + '<use xlink:href="shapes.svg#box" x="30" y="30"/></svg>', encoding="utf-8")
    pixels = svg.Document.open(page).rasterize()
    assert pixels[35, 35].round(2).tolist() == [0.0, 0.0, 1.0, 1.0]


def test_image_linking_back_to_its_own_file_is_skipped(tmp_path):
    page = tmp_path / "loop.svg"
    page.write_text(HEAD + '<rect width="10" height="10" fill="lime"/>'
                    '<image xlink:href="loop.svg" x="50" y="50" width="40" height="40"/></svg>', encoding="utf-8")
    pixels = svg.Document.open(page).rasterize()
    assert pixels[5, 5].round(2).tolist() == [0.0, 1.0, 0.0, 1.0]
