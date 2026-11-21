import numpy as np
import pytest

import svgwriter as svg
from svgwriter.formats.export import find_importer


def _round_trip(doc):
    return find_importer("pdf").function(svg.export.export(doc, "pdf"))


def test_gradients_come_back_as_gradients():
    doc = svg.Document(120, 60)
    doc.rect(5, 5, 50, 50, fill=svg.LinearGradient(svg.Stop(0, "red"), svg.Stop(0.5, "gold"), svg.Stop(1, "blue")))
    doc.circle(90, 30, 20, fill=svg.RadialGradient(svg.Stop(0, "white"), svg.Stop(1, "navy")))
    back = _round_trip(doc)
    tags = [e.tag for e in back.root.iter()]
    assert "linearGradient" in tags and "radialGradient" in tags
    assert len(list(back.root.iter("stop"))) == 5
    difference = np.abs(back.rasterize(background="white") - doc.rasterize(background="white"))
    assert difference.mean() < 0.01


def test_tiling_patterns_come_back_and_render():
    dots = svg.Pattern(svg.circle(5, 5, 3, fill="crimson"), width=10, height=10, pattern_units="userSpaceOnUse")
    doc = svg.Document(100, 60)
    doc.circle(30, 30, 25, fill=dots, stroke="black")
    back = _round_trip(doc)
    assert any(e.tag == "pattern" for e in back.root.iter())
    difference = np.abs(back.rasterize(scale=2, background="white") - doc.rasterize(scale=2, background="white"))
    assert difference.mean() < 0.03


def test_images_honour_clips_of_their_groups():
    doc = svg.Document(40, 40)
    group = doc.group()
    group.add(svg.Image(np.ones((4, 4, 3)) * [1, 0, 0], 0, 0, 40, 40))
    group.clip(svg.circle(20, 20, 10))
    pixels = doc.rasterize(background="white")
    assert pixels[20, 20].tolist() == pytest.approx([1, 0, 0, 1]) and pixels[2, 2].tolist() == pytest.approx([1, 1, 1, 1])


def test_contains_point_accepts_points_and_arrays():
    ring = svg.circle(0, 0, 10) - svg.circle(0, 0, 5)
    assert ring.contains_point(7, 0) and not ring.contains_point((0, 0))
    assert ring.contains_point(svg.Point(0, 8))
    assert ring.contains_point(np.array([[7, 0], [0, 0], [20, 0]])).tolist() == [True, False, False]
