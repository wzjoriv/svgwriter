"""numpy pixels next to vectors, then one drawing exported to every registered format.

Usage: python pixels_and_formats.py [OUTPUT_DIR]
"""

from __future__ import annotations

import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

import svgwriter as svg

SIZE = 128


def plasma(size: int) -> np.ndarray:
    y, x = np.mgrid[0:size, 0:size] / size
    value = np.sin(10 * x) + np.sin(10 * y + 2) + np.sin(10 * np.hypot(x - 0.5, y - 0.5))
    phase = (value - value.min()) / np.ptp(value)
    return np.dstack([phase, 1 - phase, 0.5 + 0.5 * np.sin(6 * phase)])


def build() -> svg.Document:
    doc = svg.Document(320, 180)
    doc.rect(0, 0, 320, 180, fill="#111827")

    picture = svg.Image(plasma(SIZE), 20, 20, 140, 140)
    y, x = np.mgrid[0:SIZE, 0:SIZE] / SIZE
    picture.alpha = np.clip(1.6 - 2.4 * np.hypot(x - 0.5, y - 0.5), 0, 1)
    doc += picture.rotate(-6)

    vector = doc.group(stroke="#f9fafb", stroke_width=3, fill="none")
    vector.add(svg.circle(240, 90, 50))
    vector.add(svg.builder.gear(240, 90, 32, teeth=12, fill="#f59e0b", stroke="none"))
    snapshot = vector.to_image(scale=0.5)
    doc += snapshot.place(240, 155) * 0.35
    return doc


def main(out_dir: Path) -> Path:
    doc = build()
    target = out_dir / "pixels_and_formats.svg"
    doc.save(target)
    formats = out_dir / "formats"
    formats.mkdir(exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, exporter in svg.export.exporters().items():
            extension = exporter.extensions[0] if exporter.extensions else f".{name}"
            doc.save(formats / f"drawing{extension}", format=name)
    return target


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix="svgwriter-"))
    print(main(folder))
