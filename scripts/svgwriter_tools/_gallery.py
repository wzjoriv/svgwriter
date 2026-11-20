"""
README gallery: run the examples and render their pictures to PNG.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

__all__ = ["GALLERY", "GALLERY_DIR", "build_gallery"]

ROOT = Path(__file__).resolve().parents[2]
GALLERY_DIR = ROOT / "docs" / "_static" / "examples"
GALLERY = {
    "basic_shapes": "basic_shapes.svg",
    "transforms": "transforms.svg",
    "boolean_ops": "boolean_ops.svg",
    "typography": "typography.svg",
    "filter_effects": "filter_effects.svg",
    "paths_and_markers": "paths_pretty.svg",
    "pixels_and_formats": "pixels_and_formats.svg",
}
SCALE = 2.0


def build_gallery(out: Path = GALLERY_DIR, scale: float = SCALE) -> list[Path]:
    """Run each gallery example into a temporary folder and save its picture as ``<example>.png`` in *out*."""
    import svgwriter as svg

    out.mkdir(parents=True, exist_ok=True)
    written = []
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    with tempfile.TemporaryDirectory(prefix="svgwriter-gallery-") as work:
        for example, picture in GALLERY.items():
            script = ROOT / "examples" / f"{example}.py"
            subprocess.run([sys.executable, str(script), work], cwd=work, env=env, check=True, capture_output=True)
            target = out / f"{example}.png"
            svg.Document.open(Path(work) / picture).save(target, scale=scale)
            written.append(target)
    return written
