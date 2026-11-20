import pytest

import svgwriter as svg

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")


def test_elements_become_editable_patches():
    import matplotlib.pyplot as plt

    doc = svg.Document(120, 60)
    doc.circle(90, 30, 20, fill=(0, 0.5, 0.5, 0.6), stroke="black", stroke_width=2)
    doc.path(fill="none", stroke="red").move_to(0, 0).curve_to(10, 20, 30, 20, 40, 0)
    fig, ax = plt.subplots()
    artists = svg.ops.to_matplotlib(doc, ax)
    assert len(artists) == 2 and ax.yaxis_inverted()
    circle, curve = artists
    assert circle.get_facecolor()[3] == pytest.approx(0.6) and circle.get_linewidth() == pytest.approx(1.5)
    assert curve.get_facecolor()[3] == 0 and 4 in curve.get_path().codes
    plt.close(fig)


def test_single_element_and_round_trip_into_a_document():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    svg.ops.to_matplotlib(svg.rect(0, 0, 10, 5, fill="teal"), ax, flip=False)
    doc = svg.Document(200, 200)
    doc.add(fig)
    assert any(e.tag == "path" for e in doc.root.iter())
    plt.close(fig)
