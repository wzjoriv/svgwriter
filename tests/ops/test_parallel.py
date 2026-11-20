import numpy as np

import svgwriter as svg
from svgwriter.ops import rasterize_many


def _docs(count):
    docs = []
    for i in range(count):
        doc = svg.Document(20, 10)
        doc.rect(i, 0, 5, 10, fill="red")
        docs.append(doc)
    return docs


def test_matches_single_process_rendering():
    docs = _docs(4)
    pooled = rasterize_many(docs, processes=2)
    for doc, pixels in zip(docs, pooled, strict=True):
        np.testing.assert_allclose(pixels, doc.rasterize(), atol=1 / 255)


def test_uint8_output():
    frames = rasterize_many(_docs(3), processes=1, dtype=np.uint8)
    assert frames[0].dtype == np.uint8 and frames[0][5, 2].tolist() == [255, 0, 0, 255]


def test_animated_export_with_processes():
    doc = svg.Document(40, 20)
    ball = doc.circle(4, 10, 4, fill="red")
    ball.append(svg.Animate(attribute_name="cx", from_=4, to=36, dur=1))
    assert svg.export.export(doc, "gif", fps=4, processes=2) == svg.export.export(doc, "gif", fps=4)
