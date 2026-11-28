"""Every project in ``demos/`` builds, and each output is a valid file of its kind."""

from __future__ import annotations

import io
import re
import shutil
import struct
import zipfile
from pathlib import Path

import pytest
import tomlkit

import svgwriter as svg

from ..conftest import wellformed

DEMOS = Path(__file__).resolve().parents[2] / "demos"
NAMES = sorted(path.name for path in DEMOS.iterdir() if (path / "svgwriter.toml").is_file())
QUICK = {"gif": {"fps": 2, "scale": 0.25}, "mp4": {"fps": 4}, "svg": {"fps": 4}, "pptx": {"fps": 4}}
"""Small frame rates and sizes, so the animated outputs stay quick to build."""
MM_PER_POINT = 25.4 / 72
A4_MM = (210, 297)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _quick_copy(name: str, folder: Path) -> svg.Project:
    """The demo copied into *folder* with quick animation settings, and MP4 swapped for GIF without ffmpeg."""
    root = folder / name
    shutil.copytree(DEMOS / name, root, ignore=shutil.ignore_patterns("output", "__pycache__"))
    manifest = root / "svgwriter.toml"
    document = tomlkit.parse(manifest.read_text(encoding="utf-8"))
    outputs = document["outputs"]
    formats = [str(format) for format in outputs["formats"]]
    if shutil.which("ffmpeg") is None:
        formats = ["gif" if format == "mp4" else format for format in formats]
    outputs["formats"] = formats
    for format, options in QUICK.items():
        if format in formats and (format != "svg" or format in outputs):
            outputs[format] = {**dict(outputs.get(format, {})), **options}
    manifest.write_text(tomlkit.dumps(document), encoding="utf-8")
    return svg.Project.load(root)


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data.startswith(PNG_SIGNATURE)
    return struct.unpack(">II", data[16:24])


def _pdf_pages_mm(path: Path) -> list[tuple[float, float]]:
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    boxes = re.findall(rb"/MediaBox \[([-\d. ]+)\]", data)
    sizes = []
    for box in boxes:
        x0, y0, x1, y1 = map(float, box.split())
        sizes.append(((x1 - x0) * MM_PER_POINT, (y1 - y0) * MM_PER_POINT))
    return sizes


def _check(path: Path) -> None:
    """Fail unless *path* is a valid, non-empty file of the kind its extension names."""
    assert path.is_file() and path.stat().st_size > 0, path
    kind = path.suffix.lower()
    if kind == ".svg":
        assert wellformed(path.read_text(encoding="utf-8")).tag.endswith("svg")
    elif kind == ".png":
        assert min(_png_size(path)) > 0
    elif kind == ".pdf":
        assert _pdf_pages_mm(path)
    elif kind == ".gif":
        assert path.read_bytes()[:6] in (b"GIF87a", b"GIF89a")
    elif kind == ".pptx":
        pptx = pytest.importorskip("pptx")
        assert len(pptx.Presentation(io.BytesIO(path.read_bytes())).slides) >= 1
    elif kind == ".mp4":
        assert b"ftyp" in path.read_bytes()[:32]
    else:
        assert zipfile.is_zipfile(path) or path.stat().st_size > 0


@pytest.mark.parametrize("name", NAMES)
def test_demo_builds(name: str, tmp_path: Path) -> None:
    project = _quick_copy(name, tmp_path)
    written = project.build()
    expected = set(project.config.formats)
    assert {path.suffix.lstrip(".") for path in written} == expected
    for path in written:
        _check(path)


def test_every_demo_has_a_readme_and_the_project_layout() -> None:
    assert len(NAMES) >= 6
    for name in NAMES:
        root = DEMOS / name
        for part in ("README.md", "theme.toml", "components", "animations", "assets", ".gitignore"):
            assert (root / part).exists(), f"{name}: no {part}"
        assert (root / "main.py").is_file() or (root / "main.ipynb").is_file()


def test_poster_is_true_a4_and_300_dpi(tmp_path: Path) -> None:
    project = _quick_copy("poster", tmp_path)
    pdf, png = project.build(["pdf", "png"])
    (width, height), = _pdf_pages_mm(pdf)
    assert (round(width), round(height)) == A4_MM
    dots = 300 / 25.4
    assert _png_size(png) == pytest.approx((A4_MM[0] * dots, A4_MM[1] * dots), abs=3)


def test_poster_invitation_shows_its_details(tmp_path: Path) -> None:
    project = _quick_copy("poster", tmp_path)
    assert {"title", "date", "time", "place"} <= set(project.controls())
    values = {"title": "Dune Planting", "date": "Sunday 5 April 2026", "place": "North end"}
    text = project.build(["svg"], values=values)[0].read_text(encoding="utf-8")
    assert all(value in text for value in values.values()) and "What to bring" in text


def test_planets_lesson_writes_one_deck_with_a_quiz_trigger(tmp_path: Path) -> None:
    import zipfile

    pytest.importorskip("pptx")
    project = _quick_copy("planets-explainer", tmp_path)
    (deck,) = project.build(["pptx"])
    slides = sorted(name for name in zipfile.ZipFile(deck).namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
    assert deck.name == "planets-explainer.pptx" and len(slides) == 4
    assert "interactiveSeq" in zipfile.ZipFile(deck).read(slides[-1]).decode()


def test_playing_card_has_controls_and_a_sweep(tmp_path: Path) -> None:
    project = _quick_copy("playing-card", tmp_path)
    assert {"rank", "suit", "hue", "iridescence", "glow", "radius", "width"} <= set(project.controls())
    names = [path.name for path in project.build(["gif"])]
    assert names == ["playing-card.gif", "playing-card-sweep.gif"]
    narrow, wide = (_png_size(project.build(["png"], values={"width": width})[0]) for width in (160, 320))
    assert narrow[0] < wide[0]


def test_light_outputs_are_committed() -> None:
    """Each demo keeps its SVG, PDF, PNG and PPTX outputs in output/ so readers can open them."""
    light = {"svg", "pdf", "png", "pptx"}
    for name in NAMES:
        formats = set(svg.Project.load(DEMOS / name).config.formats) & light
        present = {path.suffix[1:] for path in (DEMOS / name / "output").glob("*")}
        assert formats <= present, f"{name}: run `python scripts/dev.py svgwriter demo-outputs build`"
