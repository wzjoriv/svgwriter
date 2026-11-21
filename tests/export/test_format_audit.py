import warnings

import pytest

import svgwriter as svg
from tests.export.formats_drawing import formats_drawing, score

ROUND_TRIP_LIMITS = {
    "svg": 0.1, "svgz": 0.1, "html": 0.1, "png": 0.1, "pdf": 0.5, "pptx": 0.5, "docx": 0.5, "eps": 2.0,
    "excalidraw": 2.5, "tikz": 3.5, "dxf": 16.0, "hpgl": 16.0, "gcode": 16.0,
}
OFFICE = ("pptx", "docx")


@pytest.fixture(scope="module")
def drawing():
    doc = formats_drawing(formula=False)
    return doc, doc.rasterize()


@pytest.mark.parametrize(("format", "limit"), ROUND_TRIP_LIMITS.items())
def test_the_feature_drawing_survives_a_round_trip(drawing, tmp_path, format, limit):
    if format in OFFICE:
        pytest.importorskip(format)
    doc, reference = drawing
    path = tmp_path / f"drawing{svg.FORMATS.get(format).extensions[0]}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc.save(path)
        back = svg.Document.open(path)
    assert score(reference, back.rasterize()) < limit


def test_the_score_ignores_margins_and_resolution(drawing):
    doc, reference = drawing
    assert score(reference, doc.rasterize(scale=2, padding=20)) < 1.0
    assert score(reference, svg.Document(10, 10).rasterize(background="black")) > 50
