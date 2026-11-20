import numpy as np
import pytest

import svgwriter as svg


def test_columns_broadcast_and_keep_color_text():
    dots = svg.Circle.many(cx=np.arange(3) * 10, cy=5, r=2, fill=["red", "green", "blue"])
    assert [d.get("cx") for d in dots] == [0, 10, 20] and dots[1].get("fill") == "green"


def test_color_arrays_and_alpha():
    dots = svg.Circle.many(cx=[1, 2], cy=0, r=1, fill=np.array([[1, 0, 0, 0.5], [0, 0, 1, 1]]))
    assert dots[0].get("fill") == "#ff0000" and dots[0].get("fill-opacity") == 0.5
    assert dots[1].get("fill-opacity") == 1
    single = svg.Rect.many(x=[0, 5], y=0, width=1, height=1, fill=(0, 1, 0))
    assert {r.get("fill") for r in single} == {"#00ff00"}


def test_numpy_scalars_become_python_numbers_and_render():
    rects = svg.Rect.many(x=np.float32([1, 2]), y=0, width=1, height=1)
    assert type(rects[0].get("x")) is float
    doc = svg.Document(10, 10)
    doc.group(*rects)
    assert doc.rasterize()[0, 1, 3] > 0


def test_mismatched_columns_and_bad_colors():
    with pytest.raises(ValueError, match="lengths"):
        svg.Circle.many(cx=[1, 2], cy=[1, 2, 3])
    with pytest.raises(ValueError, match="redd"):
        svg.Circle.many(cx=[1], fill=["redd"])
