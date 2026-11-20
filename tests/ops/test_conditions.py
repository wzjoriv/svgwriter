import pytest

import svgwriter as svg

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
FEATURE = "http://www.w3.org/TR/SVG11/feature#Shape"


def _colour(body: str) -> list[float]:
    return svg.ops.rasterize(svg.Document.from_string(HEAD + body + "</svg>"))[5, 5].round(2).tolist()


@pytest.mark.parametrize(("condition", "drawn"), [
    (f'requiredFeatures="{FEATURE}"', True), ('requiredFeatures="INVALID"', False), ('requiredFeatures=""', False),
    ('requiredExtensions="http://example.org/ext"', False), ('systemLanguage="fr, en-GB"', True),
    ('systemLanguage="fr"', False),
])
def test_conditional_attributes_decide_rendering(condition, drawn):
    colour = _colour(f'<rect width="10" height="10" fill="lime" {condition}/>')
    assert colour == ([0.0, 1.0, 0.0, 1.0] if drawn else [0.0, 0.0, 0.0, 0.0])


def test_switch_renders_only_its_first_passing_child():
    body = ('<switch><desc>skipped</desc><rect width="10" height="10" fill="red" systemLanguage="fr"/>'
            '<rect width="10" height="10" fill="lime"/><rect width="10" height="10" fill="blue"/></switch>')
    assert _colour(body) == [0.0, 1.0, 0.0, 1.0]

