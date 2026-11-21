from __future__ import annotations

import numpy as np
import pytest

import svgwriter as svg
from svgwriter.widgets import Sweep


@svg.widgets.controls(width=(10, 90), color=["#0ea5e9", "#f43f5e"], tall=False)
def bar(width=20, color="#0ea5e9", tall=False):
    doc = svg.Document(100, 40)
    doc.rect(0, 0, width, 30 if tall else 10, fill=color)
    return doc


class TestValues:
    def test_ranges_lists_and_fixed(self) -> None:
        sweep = svg.sweep(bar, width=(10, 90), dur=2)
        assert sweep.values_at(0) == {"width": 10, "color": "#0ea5e9", "tall": False}
        assert sweep.values_at(1)["width"] == 50 and isinstance(sweep.values_at(1)["width"], int)
        assert sweep.values_at(5)["width"] == 90
        stepped = svg.sweep(bar, color=["#000000", "#ffffff", "#ff0000"], dur=3)
        assert [stepped.values_at(t)["color"] for t in (0, 1.5, 3)] == ["#000000", "#ffffff", "#ff0000"]

    def test_controls_as_tracks(self) -> None:
        sweep = svg.sweep(bar, width=svg.widgets.Slider(0, 100), color=svg.widgets.Segmented(["#000000", "#ffffff"]),
                          tall=svg.widgets.Toggle(), dur=1)
        assert sweep.values_at(0.5) == {"width": 50.0, "color": "#ffffff", "tall": True}
        fixed = svg.sweep(bar, width=svg.widgets.Number(33), color="#123456", dur=1)
        assert fixed.values_at(0.5) == {"width": 33, "color": "#123456", "tall": False}
        assert fixed.tracks == {}

    def test_kinds_and_ease(self) -> None:
        def anything(doc, size=None, tone=None):
            doc.rect(0, 0, 1, 1)

        lengths = svg.sweep(anything, size=(svg.mm(0), svg.mm(10)), tone=(svg.Color(0, 0, 0), "#ffffff"), dur=1)
        assert str(lengths.values_at(0.5)["size"]) == "5mm" and lengths.values_at(0.5)["tone"] == "#808080"
        eased = svg.sweep(bar, width=(10, 90), ease="ease-in", dur=1)
        assert eased.values_at(0.5)["width"] < 50
        with pytest.raises(TypeError, match="cannot sweep"):
            svg.sweep(anything, size=(1, "a"))
        with pytest.raises(ValueError, match="one unit"):
            svg.sweep(anything, size=(svg.mm(1), svg.pt(2)))
        with pytest.raises(ValueError, match="empty"):
            svg.sweep(anything, size=[])
        with pytest.raises(TypeError, match="no parameter"):
            svg.sweep(bar, height=(1, 2))
        with pytest.raises(ValueError, match="positive"):
            svg.sweep(bar, dur=0)


class TestScene:
    def test_frames_match_fresh_drawings(self) -> None:
        sweep = svg.sweep(bar, width=(10, 90), color=("#000000", "#ff0000"), dur=1, fps=4)
        frames = list(sweep.frames())
        assert [frame.index for frame in frames] == [0, 1, 2, 3] and (frames[0].width, frames[0].height) == (100, 40)
        for frame, seconds in zip(frames, (0, 0.25, 0.5, 0.75), strict=True):
            pixels = np.frombuffer(frame.data, np.uint8).reshape(frame.height, frame.width, 4) / 255
            expected = np.asarray(bar(**sweep.values_at(seconds)).rasterize(background="white"), dtype=float)
            expected = expected / 255 if expected.max() > 1 else expected
            assert not frame.png and np.allclose(pixels, expected, atol=2 / 255)

    def test_elements_keep_identity_and_bake(self) -> None:
        sweep = svg.sweep(bar, width=(10, 90), dur=1, fps=4)
        rect = sweep.document.root[0]
        sweep.update(0.5)
        assert sweep.document.root[0] is rect and rect.get("width") == 50
        baked = sweep.bake()
        animate = baked.root[0].children[0]
        assert animate.tag == "animate" and animate.get("attributeName") == "width"
        assert animate.get("values").split(";")[0] == "10"
        assert baked.at(1.0).root[0].get("width") in (90, "90")

    def test_structure_changes_and_elements(self, tmp_path) -> None:
        def dots(n=1):
            group = svg.group()
            for index in range(n):
                group.append(svg.circle(10 + 20 * index, 10, 5))
            return group

        sweep = svg.sweep(dots, n=[1, 2, 3], dur=3, fps=2)
        box = sweep.document.root.get("viewBox")
        assert (box.min_x, box.width) == (5, 50) and (sweep.width, sweep.height) == (50, 10)
        sweep.update(2.9)
        assert len(sweep.document.root[0]) == 3
        assert repr(sweep) == "<Sweep 'dots' 50x10 at 2 fps>"
        target = sweep.save(tmp_path / "dots.svg")
        svg.parse(target.read_text(encoding="utf-8"))

    def test_saves(self, tmp_path) -> None:
        sweep = svg.sweep(bar, width=(10, 90), dur=0.5, fps=4)
        gif = sweep.save(tmp_path / "bar.gif")
        assert gif.read_bytes()[:6] == b"GIF89a"
        assert "<animate" in sweep.save(tmp_path / "bar.svg").read_text(encoding="utf-8")
        pytest.importorskip("pptx")
        with pytest.warns(UserWarning, match="PowerPoint cannot play"):
            assert sweep.save(tmp_path / "bar.pptx").stat().st_size > 0
        assert isinstance(sweep, svg.Scene) and isinstance(sweep, Sweep)
        assert "<animate" in sweep._repr_svg_()
