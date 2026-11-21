from __future__ import annotations

from pathlib import Path

import pytest

import svgwriter as svg
from svgwriter.motion.video import Scene, SceneError, load_scenes

SCRIPT = '''
import svgwriter as svg
from svgwriter.motion.video import Scene as Imported

class _Base(svg.Scene):
    width = height = 8

class Intro(_Base):
    pass

class Outro(_Base):
    duration = 2.0

drawing = svg.Document(4, 4)
ready = Intro(name="ready")
'''


@pytest.fixture
def script(tmp_path: Path) -> Path:
    path = tmp_path / "scenes.py"
    path.write_text(SCRIPT, encoding="utf-8")
    return path


def test_every_defined_public_subclass_in_order(script: Path) -> None:
    assert [s.name for s in load_scenes(script)] == ["Intro", "Outro"]


def test_names_and_colon_reference(script: Path) -> None:
    assert [s.name for s in load_scenes(script, ["Outro", "Intro"])] == ["Outro", "Intro"]
    assert [s.name for s in load_scenes(f"{script}:Outro")] == ["Outro"]
    assert [s.name for s in load_scenes(f"{script}:Outro", ["Intro"])] == ["Outro", "Intro"]


def test_instances_and_documents(script: Path) -> None:
    ready, drawing = load_scenes(script, ["ready", "drawing"])
    assert ready.name == "ready" and drawing.name == "drawing" and isinstance(drawing, Scene)


def test_module_reference() -> None:
    (scene,) = load_scenes("tests.video.test_scene:Orbit")
    assert scene.name == "Orbit"
    assert [s.name for s in load_scenes("tests.video.test_scene")] == ["Orbit"]


def test_svg_file(tmp_path: Path) -> None:
    target = tmp_path / "pic.svg"
    doc = svg.Document(6, 6)
    doc.circle(3, 3, 1)
    doc.save(target)
    (scene,) = load_scenes(target)
    assert scene.name == "pic" and scene.document.root.find(svg.Circle) is not None


def test_errors(script: Path, tmp_path: Path) -> None:
    with pytest.raises(SceneError, match="'Missing'"):
        load_scenes(script, ["Missing"])
    with pytest.raises(SceneError, match="'Imported'"):
        load_scenes(script, ["Imported"])
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(SceneError, match="defines no"):
        load_scenes(empty)
