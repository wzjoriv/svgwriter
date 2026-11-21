from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.errors import FFmpegNotFoundError
from svgwriter.motion.video import Scene


class Orbit(svg.Scene):
    width, height, fps, duration = 20, 10, 4, 1.0

    def build(self, doc: svg.Document) -> None:
        self.dot = doc.circle(0, 5, 2)

    def update(self, seconds: float) -> None:
        self.dot.cx = 20 * seconds


def test_defaults() -> None:
    scene = Scene()
    assert (scene.width, scene.height, scene.fps, scene.duration, scene.renderer) == (640, 360, 30, None, "skia")
    assert scene.name == "Scene" and len(scene.document) == 0
    assert repr(Orbit()) == "<Orbit 'Orbit' 20x10 at 4 fps>"


def test_build_runs_once_with_class_size() -> None:
    scene = Orbit()
    assert scene.document is scene.document
    assert scene.document.root.get("viewBox").width == 20


def test_frames_call_update_with_absolute_time() -> None:
    scene = Orbit()
    seen = []
    scene.update = lambda seconds: seen.append(seconds)  # type: ignore[method-assign]
    frames = list(scene.frames())
    assert [f.index for f in frames] == [0, 1, 2, 3] and seen == [0, 0.25, 0.5, 0.75]
    assert len(list(scene.frames(fps=2, duration=2))) == 4


def test_render_moves_and_plays_smil() -> None:
    scene = Orbit()
    assert scene.render(0.5).startswith(b"\x89PNG") and scene.dot.cx == 10
    doc = svg.Document(10, 10)
    doc.circle(5, 5, 1).append(svg.Animate(attribute_name="r", from_=1, to=4, dur=1))
    smil = Scene(doc, name="pulse")
    assert smil.name == "pulse" and len(list(smil.frames())) == 30


def test_duration_required_without_smil() -> None:
    with pytest.raises(ValueError, match="duration"):
        next(Scene(svg.Document(4, 4)).frames())


def test_notebook_display_is_the_animated_svg() -> None:
    doc = svg.Document(10, 10)
    doc.circle(5, 5, 1).animate.fade_in(1)
    scene = Scene(doc)
    assert scene._repr_svg_() == doc._repr_svg_() and "<animate" in scene._repr_svg_()
    assert scene._repr_html_() == doc._repr_html_()


def test_save_defaults_to_name_mp4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FFmpegNotFoundError):
        Orbit().save(ffmpeg="no-such-ffmpeg-xyz")
    if shutil.which("ffmpeg"):
        assert Orbit().save() == Path("Orbit.mp4") and (tmp_path / "Orbit.mp4").stat().st_size > 0
        assert Orbit().save("frames.png", renderer="skia").name == "frames_%04d.png"
        assert len(list(tmp_path.glob("frames_*.png"))) == 4
