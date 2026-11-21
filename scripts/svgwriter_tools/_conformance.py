"""Round-trip and render scores against the W3C SVG 1.1 SE test suite."""

from __future__ import annotations

import fnmatch
import gzip
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import svgwriter as svg
from svgwriter.model.elements.animation import AnimationElement
from svgwriter.model.elements.structure import Pixels
from svgwriter.ops.render import render_svg

OUT_OF_SCOPE_CHAPTERS = {"script": "scripting", "interact": "interactivity and events", "extend": "foreignObject",
                         "svgdom": "SVG DOM"}
OUT_OF_SCOPE_MARKERS = {b"<script": "scripting", b"foreignObject": "foreignObject"}
CHANNEL_TOLERANCE = 64
PASS_MISMATCH = 0.01
NEIGHBOURHOOD = 1
SUITE_SIZE = (480, 360)
BACKGROUND = "white"
CHANNEL_MAX = 255
REVISION_ID = "revision"
REVISION_MARGIN = 40
WATERMARK_ID = "draft-watermark"
WATERMARK_MARGIN = 2
SETTLED_TIME = 100.0


@dataclass
class Outcome:
    """One test's round-trip and render results."""

    name: str
    chapter: str
    results: dict[str, tuple[str, float, str]] = field(default_factory=dict)
    seconds: float = 0.0

    def status(self, kind: str) -> str:
        return self.results.get(kind, ("skipped", 1.0, ""))[0]


def _box_blur(img: np.ndarray) -> np.ndarray:
    padded = np.pad(img.astype(np.float32), ((1, 1), (1, 1), (0, 0)), mode="edge")
    h, w = img.shape[:2]
    return sum(padded[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)) / 9.0


def mismatch(rendered: np.ndarray, reference: np.ndarray) -> float:
    """Fraction of pixels differing by more than the tolerance from every nearby reference pixel (0..255 RGB)."""
    h, w = reference.shape[:2]
    if rendered.shape[:2] != (h, w):
        return 1.0
    a, b = _box_blur(rendered[..., :3]), _box_blur(reference[..., :3])
    bad = np.ones((h, w), dtype=bool)
    padded = np.pad(b, ((NEIGHBOURHOOD, NEIGHBOURHOOD), (NEIGHBOURHOOD, NEIGHBOURHOOD), (0, 0)), mode="edge")
    for dy in range(2 * NEIGHBOURHOOD + 1):
        for dx in range(2 * NEIGHBOURHOOD + 1):
            bad &= np.abs(a - padded[dy:dy + h, dx:dx + w]).max(axis=-1) > CHANNEL_TOLERANCE
    return float(bad.mean())


def _rgb(pixels: np.ndarray) -> np.ndarray:
    rgba = pixels.astype(np.float32) * (CHANNEL_MAX if pixels.dtype != np.uint8 else 1)
    alpha = rgba[..., 3:4] / CHANNEL_MAX
    return rgba[..., :3] * alpha + CHANNEL_MAX * (1 - alpha)


def _bbox(doc: svg.Document, name: str) -> object | None:
    label = doc.get_element_by_id(name)
    try:
        return label.exact_bbox() if label is not None else None
    except (TypeError, ValueError):
        return None


def label_boxes(doc: svg.Document, shape: tuple[int, ...]) -> list[tuple[slice, slice]]:
    """Pixels of the suite's bookkeeping labels, which differ between a test and its PNG.

    The ``$Revision$`` label names the file version and the ``DRAFT`` watermark the review status;
    the reference PNGs often predate both.
    """
    boxes = []
    box = _bbox(doc, REVISION_ID)
    if box is not None:
        rows = slice(max(int(box.y) - REVISION_MARGIN // 4, 0),
                     min(int(box.y + box.height) + REVISION_MARGIN // 4, shape[0]))
        boxes.append((rows, slice(0, min(int(box.x + box.width) + REVISION_MARGIN, shape[1]))))
    box = _bbox(doc, WATERMARK_ID)
    if box is not None:
        boxes.append((slice(0, min(int(box.y + box.height) + WATERMARK_MARGIN, shape[0])), slice(0, shape[1])))
    return boxes


def _scope(name: str, data: bytes) -> str | None:
    chapter = name.split("-", 1)[0]
    if chapter in OUT_OF_SCOPE_CHAPTERS:
        return OUT_OF_SCOPE_CHAPTERS[chapter]
    if "-dom-" in name:
        return "SVG DOM"
    return next((reason for marker, reason in OUT_OF_SCOPE_MARKERS.items() if marker in data), None)


def _grade(frac: float) -> tuple[str, float, str]:
    return ("pass" if frac <= PASS_MISMATCH else "fail", frac, "")


def run_test(path: Path, reference: Path) -> Outcome:
    """Score one suite file."""
    name = path.name.split(".")[0]
    outcome = Outcome(name, name.split("-", 1)[0])
    data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    reason = _scope(name, data)
    if reason:
        outcome.results = {"roundtrip": ("skipped", 1.0, reason), "render": ("skipped", 1.0, reason)}
        return outcome
    start = time.perf_counter()
    width, height = SUITE_SIZE
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            doc = svg.Document.open(path)
            written = doc.to_string()
        except Exception as exc:  # noqa: BLE001
            note = f"{type(exc).__name__}: {exc}"
            outcome.results = {"roundtrip": ("error", 1.0, note), "render": ("error", 1.0, note)}
            return outcome
        try:
            original = render_svg(data.decode("utf-8", "replace"), width, height, background=BACKGROUND)
        except ValueError:
            outcome.results["roundtrip"] = ("skipped", 1.0, "skia cannot read the original file")
        else:
            try:
                again = render_svg(written, width, height, background=BACKGROUND)
                outcome.results["roundtrip"] = _grade(mismatch(_rgb(again), _rgb(original)))
            except Exception as exc:  # noqa: BLE001
                outcome.results["roundtrip"] = ("error", 1.0, f"{type(exc).__name__}: {exc}")
        try:
            if reference.exists():
                expected = Pixels.decode(reference.read_bytes()).rgba()
                shown = doc.at(SETTLED_TIME) if doc.root.find(AnimationElement) is not None else doc
                drawn = _rgb(svg.ops.rasterize(shown, pixels=(expected.shape[1], expected.shape[0]), background=BACKGROUND))
                expected = _rgb(expected)
                for label in label_boxes(doc, expected.shape):
                    drawn[label] = expected[label]
                outcome.results["render"] = _grade(mismatch(drawn, expected))
        except Exception as exc:  # noqa: BLE001
            outcome.results["render"] = ("error", 1.0, f"{type(exc).__name__}: {exc}")
    outcome.seconds = time.perf_counter() - start
    return outcome


def run_suite(suite: Path, pattern: str = "", echo: Callable[[str], object] | None = None) -> list[Outcome]:
    """Run every (or every matching) test in *suite*."""
    tests = sorted(p for p in (suite / "svg").iterdir() if p.suffix in (".svg", ".svgz"))
    if pattern:
        glob = pattern if any(c in pattern for c in "*?[") else f"*{pattern}*"
        tests = [t for t in tests if fnmatch.fnmatch(t.name, glob)]
    outcomes = []
    for path in tests:
        outcome = run_test(path, suite / "png" / (path.name.split(".")[0] + ".png"))
        outcomes.append(outcome)
        if echo is not None:
            for kind, (status, frac, note) in outcome.results.items():
                if status in ("fail", "error"):
                    echo(f"{kind:9} {status:5} {outcome.name} {100 * frac:.1f}% {note}")
    return outcomes


def write_report(outcomes: list[Outcome], path: Path) -> None:
    """A Markdown report with both scores, per chapter."""
    lines = ["# svgwriter conformance (W3C SVG 1.1 SE test suite)", "",
             "- **roundtrip**: the original file and svgwriter's parse-and-write output, both rendered by skia, "
             "must match. This is the writer's fidelity score.",
             "- **render**: `svgwriter.ops.rasterize` against the W3C reference PNG; bounded by skia's SVG support.",
             f"- A test passes when at most {PASS_MISMATCH:.0%} of pixels differ by more than "
             f"{CHANNEL_TOLERANCE}/255 after a 3x3 blur, within {NEIGHBOURHOOD} px. "
             "The `$Revision$` label and `DRAFT` watermark (file version and review status, which the reference "
             "PNGs often predate) are not compared. Animated tests are drawn "
             f"at {SETTLED_TIME:g} s, once their animations have settled, the state the references show.",
             ""]
    for kind in ("roundtrip", "render"):
        scored = [o for o in outcomes if o.status(kind) != "skipped"]
        ok = sum(o.status(kind) == "pass" for o in scored)
        lines += [f"## {kind}: {ok}/{len(scored)} ({100.0 * ok / max(len(scored), 1):.1f}%)", "",
                  "| Chapter | Passed | Total |", "| --- | ---: | ---: |"]
        for chapter in sorted({o.chapter for o in scored}):
            group = [o for o in scored if o.chapter == chapter]
            lines.append(f"| {chapter} | {sum(o.status(kind) == 'pass' for o in group)} | {len(group)} |")
        lines += ["", "Failures:", ""]
        for o in scored:
            status, frac, note = o.results[kind]
            if status != "pass":
                lines.append(f"- {o.name}: {status} {100 * frac:.1f}% {note.replace('|', '/')[:150]}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
