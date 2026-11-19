"""An app logo defined in Python, with variants, and every asset generated from it.

A project keeps a module like this one; tooling imports ``logo`` and writes
SVG variants, PNGs at any size, ``.ico``/``.icns`` and favicons. Output is
deterministic, so stale assets can be detected by regenerating and comparing.

Usage: python logo.py [OUTPUT_DIR]
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Literal

import svgwriter as svg

SIZE = 100.0
PADDING = 4.0
THEMES = {
    "light": {"ground": "#0f766e", "mark": "#ffffff", "accent": "#fbbf24"},
    "dark": {"ground": "#99f6e4", "mark": "#042f2e", "accent": "#b45309"},
}
PNG_SIZES = (16, 32, 48, 64, 128, 256, 512, 1024)
FAVICON_SIZES = (16, 32, 48)
APPLE_TOUCH_SIZE = 180


def logo(theme: Literal["light", "dark"] = "light", *, mono: bool = False) -> svg.Document:
    """The logo as a document; ``theme`` picks the palette and ``mono`` draws it in one color.

    Parameters
    ----------
    theme : {"light", "dark"}
        Color palette.
    mono : bool
        Single-color version (the mark is cut out of the ground).

    Returns
    -------
    Document
        A ``SIZE x SIZE`` drawing centred on the origin.
    """
    colors = THEMES[theme]
    doc = svg.Document(root=svg.Svg(view_box=(-SIZE / 2, -SIZE / 2, SIZE, SIZE)))
    ground = svg.rect(-SIZE / 2, -SIZE / 2, SIZE, SIZE, rx=SIZE * 0.22)
    pen = svg.path().move_to(-22, 18).line_to(0, -24).line_to(22, 18)
    mark = pen.to_path(stroke="black", stroke_width=12, fill="none").stroked(12)
    dot = svg.circle(0, 6, 7)
    if mono:
        doc += (ground - mark - dot).update(fill=colors["ground"])
        return doc
    doc += ground.update(fill=colors["ground"])
    doc += mark.update(fill=colors["mark"])
    doc += dot.update(fill=colors["accent"])
    return doc


def write_assets(out_dir: Path) -> list[Path]:
    """Every asset a project usually needs, from the one definition above."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for theme in THEMES:
        target = out_dir / f"logo-{theme}.svg"
        logo(theme).save(target)
        written.append(target)
    target = out_dir / "logo-mono.svg"
    logo(mono=True).save(target)
    written.append(target)
    light = logo()
    for size in PNG_SIZES:
        target = out_dir / f"logo-{size}.png"
        light.save(target, size=size, padding=PADDING)
        written.append(target)
    for name, options in {
        "favicon.ico": {"sizes": FAVICON_SIZES},
        "logo.icns": {},
        "apple-touch-icon.png": {"size": APPLE_TOUCH_SIZE, "background": THEMES["light"]["ground"]},
    }.items():
        target = out_dir / name
        light.save(target, padding=PADDING, **options)
        written.append(target)
    return written


def main(out_dir: Path) -> Path:
    write_assets(out_dir)
    return out_dir


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="svgwriter-"))
    for path in write_assets(folder):
        print(path)
