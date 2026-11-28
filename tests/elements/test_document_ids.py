import re

import svgwriter as svg


def _drawing() -> str:
    doc = svg.Document(width=60, height=30)
    doc.rect(5, 5, 50, 20, filter=svg.filters.drop_shadow(), fill=svg.LinearGradient.horizontal("red", "blue"))
    return doc.to_string()


def test_output_does_not_depend_on_what_was_made_before():
    first = _drawing()
    for _ in range(3):
        svg.filters.glow(2)
        svg.LinearGradient.horizontal("white", "black")
    assert _drawing() == first


def test_filter_results_number_within_the_document_and_inputs_follow():
    text = _drawing()
    results = set(re.findall(r'result="([^"]+)"', text))
    inputs = {name for name in re.findall(r'in2?="([^"]+)"', text) if name.endswith("-out")}
    assert inputs <= results and "feGaussianBlur1-out" in results
