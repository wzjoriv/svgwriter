"""
README gallery: run the examples and render their pictures to PNG (animated ones are copied as GIF).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

__all__ = ["GALLERY", "GALLERY_DIR", "Picture", "build_gallery"]

ROOT = Path(__file__).resolve().parents[2]
GALLERY_DIR = ROOT / "docs" / "_static" / "examples"
SCALE = 2.0
OUT_VARIABLE = "SVGWRITER_EXAMPLES_OUT"


class Picture(NamedTuple):
    """One gallery picture: the example that makes it, the file it saves and how to render it."""

    example: str
    file: str
    background: str | None = None
    padding: float = 0.0


GALLERY = {
    "basic_shapes": Picture("basic_shapes", "basic_shapes.svg"),
    "transforms": Picture("transforms", "transforms.svg"),
    "boolean_ops": Picture("boolean_ops", "boolean_ops.svg"),
    "typography": Picture("typography", "typography.svg"),
    "filter_effects": Picture("filter_effects", "filter_effects.svg"),
    "paths_and_markers": Picture("paths_and_markers", "paths_pretty.svg"),
    "animation": Picture("animation", "animation.gif"),
    "math": Picture("math_and_diagrams", "math.svg"),
    "flowchart": Picture("math_and_diagrams", "flowchart.svg", background="white", padding=12),
}


def build_gallery(out: Path = GALLERY_DIR, scale: float = SCALE) -> list[Path]:
    """Run each gallery example into a temporary folder and write its picture to *out*.

    Parameters
    ----------
    out : Path, optional
        Destination folder. Defaults to ``docs/_static/examples``.
    scale : float, optional
        Raster scale of the PNGs. Defaults to 2.

    Returns
    -------
    list of Path
        The files written: ``<name>.png``, or ``<name>.gif`` for an animated picture.
    """
    import svgwriter as svg

    out.mkdir(parents=True, exist_ok=True)
    written = []
    ran: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="svgwriter-gallery-") as work:
        env = {**os.environ, "PYTHONPATH": str(ROOT), OUT_VARIABLE: work}
        for name, picture in GALLERY.items():
            if picture.example not in ran:
                script = ROOT / "examples" / f"{picture.example}.py"
                subprocess.run([sys.executable, str(script)], cwd=work, env=env, check=True, capture_output=True)
                ran.add(picture.example)
            source = Path(work) / picture.file
            if source.suffix == ".gif":
                target = out / f"{name}.gif"
                shutil.copyfile(source, target)
            else:
                target = out / f"{name}.png"
                svg.Document.open(source).save(target, scale=scale, background=picture.background, padding=picture.padding)
            written.append(target)
    return written
