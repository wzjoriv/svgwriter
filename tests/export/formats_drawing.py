"""A drawing that exercises every feature the export formats are compared on, and the score that compares them."""

from __future__ import annotations

import numpy as np

import svgwriter as svg

WIDTH, HEIGHT = 400, 300
INK = 220 / 255


def _picture() -> np.ndarray:
    ys, xs = np.mgrid[0:24, 0:24]
    pixels = np.zeros((24, 24, 4), dtype=np.uint8)
    pixels[..., 0] = xs * 10
    pixels[..., 1] = ys * 10
    pixels[..., 2] = 160
    pixels[..., 3] = 255
    return pixels


def formats_drawing(*, formula: bool = True) -> svg.Document:
    """Build the feature drawing the format audit exports to every format.

    Parameters
    ----------
    formula : bool, optional
        Add an ``svg.latex`` formula. Defaults to True; it is skipped when no TeX engine is available.

    Returns
    -------
    Document
        A 400 x 300 drawing with fills, gradients, a pattern, strokes, opacity, a clip, text, an image,
        transforms, markers, a grid, a star and a formula.
    """
    doc = svg.Document(WIDTH, HEIGHT)
    doc.rect(0, 0, WIDTH, HEIGHT, fill="white")
    doc.add(svg.builder.grid(10, 10, 180, 120, spacing=20, stroke="#94a3b8", stroke_width=1, fill="none"))
    doc.rect(20, 20, 70, 40, fill="#ef4444", stroke="black", stroke_width=2)
    doc.rect(100, 20, 80, 40, fill=svg.LinearGradient.horizontal("#facc15", "#2563eb"))
    doc.circle(55, 100, 25, fill=svg.RadialGradient(svg.Stop(0, "white"), svg.Stop(1, "#16a34a")))
    dots = doc.define(svg.Pattern(svg.circle(5, 5, 3, fill="#7c3aed"), width=10, height=10,
                                  pattern_units="userSpaceOnUse"))
    doc.rect(100, 75, 80, 50, fill=dots, stroke="#7c3aed")
    doc.path("M210 30 L260 70 L310 30 L360 70", fill="none", stroke="#0ea5e9", stroke_width=8,
             stroke_linecap="round", stroke_linejoin="round")
    doc.path("M210 100 L370 100", fill="none", stroke="#f97316", stroke_width=5, stroke_dasharray="14 6",
             stroke_linecap="butt")
    doc.circle(240, 150, 30, fill="#ec4899", fill_opacity=0.5, stroke="#831843", stroke_width=3, stroke_opacity=0.6)
    doc.circle(270, 150, 30, fill="#3b82f6", opacity=0.5)
    clip = doc.define(svg.ClipPath(svg.circle(340, 160, 28)))
    doc.add(svg.Rect(340, 120, 40, 80, fill="#14b8a6", clip_path=clip))
    tilted = doc.add(svg.Group(transform="rotate(20 60 200)"))
    tilted.add(svg.rect(30, 180, 60, 30, fill="#a855f7", stroke="#3b0764", stroke_width=2))
    head = svg.markers.arrow(6, color="#dc2626")
    doc.path("M110 220 Q150 160 190 220", fill="none", stroke="#dc2626", stroke_width=3, marker_end=head)
    doc.add(svg.builder.star(240, 240, 35, 15, points=5, fill="#fbbf24", stroke="#92400e", stroke_width=2))
    doc.add(svg.Image(_picture(), 300, 215, 60, 60))
    title = doc.text("Formats audit", x=20, y=275, font_size=22, font_family="Helvetica", fill="#111827")
    title[8:13].wrap(fill="#be123c", font_weight="bold")
    if formula:
        try:
            equation = svg.latex(r"e^{i\pi}+1=0")
        except Exception:  # noqa: BLE001
            return doc
        equation.translate(20, 230)
        doc.add(equation)
    return doc


def on_white(pixels: np.ndarray) -> np.ndarray:
    """RGB floats in 0..1 of straight-alpha RGBA or RGB pixels (``uint8`` or 0..1 floats) laid over white."""
    values = np.asarray(pixels, dtype=np.float32)
    if pixels.dtype == np.uint8:
        values = values / 255
    if values.shape[-1] == 3:
        return values
    alpha = values[..., 3:]
    return values[..., :3] * alpha + (1 - alpha)


def _inked(pixels: np.ndarray) -> np.ndarray:
    rgb = on_white(pixels)
    ink = rgb.min(axis=2) < INK
    rows, columns = np.flatnonzero(ink.any(axis=1)), np.flatnonzero(ink.any(axis=0))
    if not len(rows):
        return rgb
    return rgb[rows[0]:rows[-1] + 1, columns[0]:columns[-1] + 1]


def score(reference: np.ndarray, candidate: np.ndarray) -> float:
    """Mean absolute difference, in percent of full scale, of the inked areas of two renderings.

    Both are laid over white and cropped to the box of their non-white pixels, and the candidate is
    sampled onto the reference's box, so margins and resolution do not count.

    Parameters
    ----------
    reference, candidate : numpy.ndarray
        RGBA or RGB pixels, as ``uint8`` or as floats in 0..1.

    Returns
    -------
    float
        0 for identical pictures, 100 for black against white everywhere.
    """
    expected, actual = _inked(reference), _inked(candidate)
    actual = _resample(_resample(actual, expected.shape[0], 0), expected.shape[1], 1)
    return float(np.abs(expected - actual).mean() * 100)


def _resample(pixels: np.ndarray, size: int, axis: int) -> np.ndarray:
    """*pixels* averaged in boxes (or repeated) along *axis* to *size* entries."""
    edges = (np.arange(size + 1) * pixels.shape[axis] / size).astype(int)
    starts = np.minimum(edges[:-1], pixels.shape[axis] - 1)
    counts = np.maximum(edges[1:] - starts, 1)
    shape = [1, 1, 1]
    shape[axis] = size
    return np.add.reduceat(pixels, starts, axis=axis) / counts.reshape(shape)
