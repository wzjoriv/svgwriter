"""
Format audit: export one feature drawing to every format, render each result and score it against the original.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import tempfile
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from svgwriter import Document

__all__ = ["FORMATS_DIR", "Result", "audit", "contact_sheet", "feature_drawing", "score", "write_report"]

ROOT = Path(__file__).resolve().parents[2]
FORMATS_DIR = ROOT / "build" / "formats"
SCALE = 2.0
GHOSTSCRIPT = ("gswin64c", "gswin32c", "gs")
TILE_LABEL = 16
RASTERS = ("png", "jpeg", "webp", "bmp", "gif", "ppm")


@dataclass
class Result:
    """One format's outcome: the rendered export, the rendered round trip and their scores."""

    name: str
    exported: np.ndarray | None = None
    exported_by: str = ""
    round_trip: np.ndarray | None = None
    error: str = ""

    def scores(self, reference: np.ndarray) -> tuple[float | None, float | None]:
        """Return the export and round-trip difference scores against *reference*."""
        return (score(reference, self.exported) if self.exported is not None else None,
                score(reference, self.round_trip) if self.round_trip is not None else None)


def _flatten(pixels: np.ndarray, size: tuple[int, int]) -> Image.Image:
    rgb = np.clip(_fixtures().on_white(pixels) * 255 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb).resize(size, Image.Resampling.LANCZOS)


def _fixtures() -> ModuleType:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tests.export import formats_drawing

    return formats_drawing


def score(reference: np.ndarray, candidate: np.ndarray) -> float:
    """The difference score of ``tests/export/formats_drawing.py``, 0 for identical renderings."""
    return _fixtures().score(reference, candidate)


def _tool(names: tuple[str, ...]) -> str | None:
    return next((found for name in names if (found := shutil.which(name))), None)


def _ghostscript(data: bytes, suffix: str, work: Path) -> np.ndarray | None:
    gs = _tool(GHOSTSCRIPT)
    if gs is None:
        return None
    source, target = work / f"in{suffix}", work / "gs.png"
    source.write_bytes(data)
    fit = ["-dEPSCrop"] if suffix == ".eps" else ["-dUseCropBox"]
    subprocess.run([gs, "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pngalpha", *fit,
                    f"-r{72 * SCALE:g}", "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", f"-sOutputFile={target}",
                    str(source)], check=True, capture_output=True, timeout=120)
    return np.asarray(Image.open(target).convert("RGBA"))


def _latex(text: str, work: Path) -> np.ndarray | None:
    latex, ppm = _tool(("pdflatex",)), _tool(("pdftoppm",))
    if latex is None or ppm is None:
        return None
    (work / "fig.tex").write_text(text, encoding="utf-8")
    subprocess.run([latex, "-interaction=nonstopmode", "-halt-on-error", "fig.tex"], cwd=work, check=True,
                   capture_output=True, timeout=180)
    subprocess.run([ppm, "-png", "-singlefile", "-r", f"{72 * SCALE:g}", "fig.pdf", "fig"], cwd=work, check=True,
                   capture_output=True, timeout=120)
    return np.asarray(Image.open(work / "fig.png").convert("RGBA"))


def _picture(data: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(data))
    if getattr(image, "n_frames", 1) > 1:
        image.seek(0)
    if image.format == "ICO":
        image.size = max(image.ico.sizes())
    return np.asarray(image.convert("RGBA"))


def _xlsx_picture(data: bytes) -> np.ndarray:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        media = next(name for name in archive.namelist() if name.startswith("xl/media/"))
        return _picture(archive.read(media))


def _rasterize(document: Document) -> np.ndarray:
    return document.rasterize(scale=SCALE)


def _render_export(name: str, data: bytes | str, work: Path, document: Document) -> tuple[np.ndarray | None, str]:
    import svgwriter as svg

    raw = data.encode() if isinstance(data, str) else data
    if name in (*RASTERS, "ico", "icns"):
        return _picture(raw), "Pillow"
    if name == "xlsx":
        return _xlsx_picture(raw), "embedded picture"
    if name in ("pdf", "eps"):
        rendered = _ghostscript(raw, f".{name}", work)
        if rendered is not None:
            return rendered, "Ghostscript"
    if name == "tikz":
        rendered = _latex(str(svg.export.export(document, "tikz", standalone=True)), work)
        if rendered is not None:
            return rendered, "pdflatex"
    if _readable(name):
        return _rasterize(_load(name, raw, work)), "svgwriter"
    return None, ""


def _readable(name: str) -> bool:
    import svgwriter as svg

    try:
        svg.export.find_importer(svg.export.exporters()[name].extensions[0])
    except ValueError:
        return False
    return True


def _load(name: str, data: bytes, work: Path) -> Document:
    import svgwriter as svg

    suffix = svg.export.exporters()[name].extensions[0]
    path = work / f"export{suffix}"
    path.write_bytes(data)
    return svg.Document.open(path)


def audit(document: Document, formats: list[str] | None = None) -> tuple[np.ndarray, list[Result]]:
    """Export *document* to every format, render each export and each round trip.

    Parameters
    ----------
    document : Document
        The drawing to audit.
    formats : list of str, optional
        Exporter names. Defaults to every registered exporter.

    Returns
    -------
    tuple of (numpy.ndarray, list of Result)
        The reference rendering and one result per format.
    """
    import svgwriter as svg

    reference = _rasterize(document)
    results = []
    for name in formats or sorted(svg.export.exporters()):
        result = Result(name)
        with tempfile.TemporaryDirectory(prefix=f"svgwriter-{name}-") as folder, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            work = Path(folder)
            try:
                options = {"scale": SCALE} if name in RASTERS else {}
                data = svg.export.export(document, name, **options)
                result.exported, result.exported_by = _render_export(name, data, work, document)
                if _readable(name):
                    raw = data.encode() if isinstance(data, str) else data
                    result.round_trip = _rasterize(_load(name, raw, work))
            except Exception as error:  # noqa: BLE001
                result.error = f"{type(error).__name__}: {error}"
        results.append(result)
    return reference, results


def _tile(pixels: np.ndarray | None, size: tuple[int, int], label: str) -> Image.Image:
    tile = Image.new("RGB", (size[0], size[1] + TILE_LABEL), "#e5e7eb")
    if pixels is not None:
        tile.paste(_flatten(pixels, size), (0, TILE_LABEL))
    ImageDraw.Draw(tile).text((4, 2), label, fill="black")
    return tile


def contact_sheet(reference: np.ndarray, results: list[Result], width: int = 400) -> Image.Image:
    """Lay out the reference, each export and each round trip in labelled rows of three.

    Parameters
    ----------
    reference : numpy.ndarray
        The original drawing's pixels.
    results : list of Result
        The audited formats.
    width : int, optional
        Width of one tile in pixels. Defaults to 400.

    Returns
    -------
    PIL.Image.Image
        One row per format: original, export, round trip.
    """
    size = (width, round(width * reference.shape[0] / reference.shape[1]))
    rows = []
    for result in results:
        exported, round_trip = result.scores(reference)
        rows.append([
            _tile(reference, size, f"{result.name}: original"),
            _tile(result.exported, size, f"export ({result.exported_by or 'not rendered'})"
                  + (f"  {exported:.2f}" if exported is not None else f"  {result.error[:50]}")),
            _tile(result.round_trip, size, "round trip" + (f"  {round_trip:.2f}" if round_trip is not None else ": -")),
        ])
    tile_w, tile_h = size[0], size[1] + TILE_LABEL
    sheet = Image.new("RGB", (3 * tile_w + 8, len(rows) * (tile_h + 4)), "white")
    for row_index, row in enumerate(rows):
        for column, tile in enumerate(row):
            sheet.paste(tile, (column * (tile_w + 4), row_index * (tile_h + 4)))
    return sheet


def write_report(reference: np.ndarray, results: list[Result], out: Path = FORMATS_DIR) -> list[Path]:
    """Write the contact sheet, one sheet per format and a Markdown score table into *out*.

    Parameters
    ----------
    reference : numpy.ndarray
        The original drawing's pixels.
    results : list of Result
        The audited formats.
    out : Path, optional
        Destination folder. Defaults to ``build/formats``.

    Returns
    -------
    list of Path
        The files written.
    """
    out.mkdir(parents=True, exist_ok=True)
    written = [out / "contact_sheet.png", out / "scores.md"]
    contact_sheet(reference, results).save(written[0])
    for result in results:
        target = out / f"{result.name}.png"
        contact_sheet(reference, [result], width=600).save(target)
        written.append(target)
    lines = ["| format | rendered by | export score | round-trip score | note |", "| --- | --- | ---: | ---: | --- |"]
    for result in results:
        exported, round_trip = result.scores(reference)
        lines.append(f"| {result.name} | {result.exported_by or '-'} | "
                     f"{'-' if exported is None else f'{exported:.2f}'} | "
                     f"{'-' if round_trip is None else f'{round_trip:.2f}'} | {result.error} |")
    written[1].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return written


def feature_drawing() -> Document:
    """The audit's feature drawing, from ``tests/export/formats_drawing.py``."""
    return _fixtures().formats_drawing()
