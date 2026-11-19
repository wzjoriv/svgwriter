"""Placement through one transform: rotate, scale, flip and place, plus boolean cut-outs.

A ring of petals is built from one shape by rotating copies about a shared pivot, then cut and clipped.

Usage: python transforms.py [OUTPUT_DIR]
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import svgwriter as svg

SIZE = 300
CENTER = (SIZE / 2, SIZE / 2)
PETALS = 12


def build() -> svg.Document:
    doc = svg.Document(SIZE, SIZE)
    doc.rect(0, 0, SIZE, SIZE, fill="#0f172a")

    petal = svg.ellipse(SIZE / 2, SIZE / 2 - 70, 18, 60, fill=svg.LinearGradient.vertical("#f472b6", "#7c3aed"))
    with doc.group(opacity=0.9):
        for i in range(PETALS):
            doc.add(petal @ 0).rotate(360 * i / PETALS, about=CENTER)

    core = svg.circle(*CENTER, 46) - svg.builder.star(*CENTER, 30, points=8)
    doc += core.update(fill="#fde047")

    badge = svg.rect.from_center((0, 0), (90, 26), rx=13, fill="#f8fafc")
    doc += badge.place(SIZE / 2, SIZE - 30)
    doc.text("transforms", x=SIZE / 2, y=SIZE - 25, font_size=14, text_anchor="middle", fill="#0f172a")

    corner = svg.builder.arrow(20, 20, 70, 20, head=10, stroke="#38bdf8", stroke_width=3)
    doc += [corner, corner.clone().flip_x(about=CENTER), corner.clone().flip_y(about=CENTER),
            corner.clone().flip_x(about=CENTER).flip_y(about=CENTER)]

    window = svg.rect(0, 0, SIZE, SIZE).clip(svg.circle(*CENTER, SIZE / 2 - 4))
    window.update(fill="none", stroke="#334155", stroke_width=8)
    doc += window
    return doc


def main(out_dir: Path) -> Path:
    target = out_dir / "transforms.svg"
    doc = build()
    doc.save(target)
    doc.save(out_dir / "transforms.png", scale=2)
    return target


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="svgwriter-"))
    print(main(folder))
