import pytest

import svgwriter as svg

zp = pytest.importorskip("ziaplot")


def test_ziaplot_plot_adds_as_editable_elements():
    with zp.Graph() as plot:
        zp.PolyLine([0, 1, 2, 3], [0, 1, 4, 9])
    doc = svg.Document(400, 300)
    added = doc.add(plot)
    assert len(list(added.iter())) > 1
    assert "<path" in doc.to_string() or "<polyline" in doc.to_string()
