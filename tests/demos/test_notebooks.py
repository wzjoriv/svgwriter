"""Each demo has a notebook of its ``main.py`` cells, and the demos' controls restyle their outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from .test_demos import NAMES, _quick_copy

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
CONTROLLED = {
    "blobs": {"count", "melt", "speed"},
    "calculator-kit": {"style", "shape", "layout", "accent"},
    "playing-card": {"rank", "suit", "hue", "iridescence"},
    "poster": {"theme", "hue", "title"},
    "effects": {"title", "first", "second", "buttons"},
}


@pytest.fixture(scope="module")
def tool():
    pytest.importorskip("typer")
    sys.path.insert(0, str(SCRIPTS))
    try:
        from svgwriter_tools import _demo_notebooks
    finally:
        sys.path.remove(str(SCRIPTS))
    return _demo_notebooks


def test_notebooks_match_their_scripts(tool) -> None:
    assert tool.stale() == []


@pytest.mark.parametrize("name", NAMES)
def test_every_demo_has_a_notebook_with_stills_for_its_controls(name: str, tool) -> None:
    assert tool.notebook_path(name).is_file()
    assert tool.controlled(name)
    assert tool.STILLS[name]


@pytest.mark.parametrize("name", sorted(CONTROLLED))
def test_page_controls_are_declared(name: str, tmp_path: Path) -> None:
    project = _quick_copy(name, tmp_path)
    assert CONTROLLED[name] <= set(project.controls())


def test_poster_controls_restyle_it(tmp_path: Path) -> None:
    project = _quick_copy("poster", tmp_path)
    plain = project.build(["svg"])[0].read_text(encoding="utf-8")
    styled = project.build(["svg"], values={"theme": "night", "hue": 90, "title": "Wave"})[0].read_text(encoding="utf-8")
    assert "Wave" in styled and "Wave" not in plain and styled != plain


def test_effect_dropdowns_swap_the_effects(tmp_path: Path) -> None:
    project = _quick_copy("effects", tmp_path)
    plain = project.build(["svg"])[0].read_text(encoding="utf-8")
    swapped = project.build(["svg"], values={"first": "ice", "second": "neon", "title": "Neon Ruins"})[0].read_text(encoding="utf-8")
    assert swapped != plain and "Ruins" in swapped and "Ruins" not in plain


def test_blobs_speed_shortens_the_loop(tmp_path: Path) -> None:
    project = _quick_copy("blobs", tmp_path)
    slow, fast = (project.build(["svg"], values={"speed": speed})[0].read_text(encoding="utf-8") for speed in (1.0, 2.0))
    assert 'dur="4s"' in slow or 'dur="4"' in slow
    assert 'dur="2s"' in fast or 'dur="2"' in fast

