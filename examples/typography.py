"""Text as live characters: styled ranges, per-glyph moves and rotations, outlines and cut-outs.

Usage: python typography.py [OUTPUT_DIR]
"""

from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

import svgwriter as svg

WIDTH, HEIGHT = 420, 220
SERIF = "Georgia, Times New Roman, serif"
SANS = "Arial, Helvetica, sans-serif"


def build() -> svg.Document:
    doc = svg.Document(WIDTH, HEIGHT)
    doc.style("text { font-family: Arial, Helvetica, sans-serif; } .accent { fill: #be123c; }")
    doc.rect(0, 0, WIDTH, HEIGHT, fill="#fffbeb")

    title = doc.text("Typography in SVG", x=20, y=50, font_size=34, font_family=SERIF, fill="#1c1917")
    title[0:10].wrap(class_="accent", font_style="italic")

    wave = doc.text("characters stay text", x=20, y=105, font_size=24, fill="#0f766e")
    for index, glyph in enumerate(wave):
        glyph.translate(0, 6 * math.sin(index / 2))
    wave[0:10].rotate(-8)

    stencil = svg.rect(20, 130, 380, 70, rx=10) - svg.text("STENCIL", x=210, y=187, font_size=56,
                                                          font_family=SANS, font_weight="bold",
                                                          text_anchor="middle")
    doc += stencil.update(fill="#1c1917")

    outlines = svg.text("glyphs", x=330, y=105, font_size=28, font_family=SERIF).glyphs()
    for index, path in enumerate(outlines):
        path.update(fill="#7c3aed").scale(1 + index * 0.08)
    doc += outlines
    return doc


def main(out_dir: Path) -> Path:
    target = out_dir / "typography.svg"
    doc = build()
    doc.save(target)
    doc.save(out_dir / "typography.png", scale=2)
    return target


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="svgwriter-"))
    print(main(folder))
