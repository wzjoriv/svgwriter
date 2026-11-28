"""
Pictures of what the docs' code snippets draw: each page's Python blocks are run in order and every block
that makes, changes or saves a drawing gets that drawing as an SVG, shown under the block by the docs build.
"""

from __future__ import annotations

import ast
import contextlib
import io
import os
import re
import tempfile
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "_snippets"
BLOCK = re.compile(r"```python\n(.*?)```", re.S)
SAVES = re.compile(r"\.(save|write|to_file)\(")
SHOWN = "__shown__"
"""List the values of a block's bare expressions are kept in."""
CANVAS_PAD = 0.08
"""Margin around a shared frame, as a share of its larger side."""
MAX_PICTURES = 4
"""Most pictures shown under one block (the last ones it draws)."""
SAMPLE = ROOT / "tests" / "export" / "data" / "sample.excalidraw"

def pages() -> list[Path]:
    """Docs pages with Python blocks."""
    return sorted(page for page in DOCS.rglob("*.md")
                  if "_build" not in page.parts and BLOCK.search(page.read_text(encoding="utf-8")))


def _names(block: str) -> list[str]:
    """Names a block assigns or uses, in order of their last appearance."""
    try:
        tree = ast.parse(block)
    except SyntaxError:
        return []
    seen = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
    return list(dict.fromkeys(reversed(seen)))


def _picture(value: Any) -> str | None:
    """The SVG a notebook would show for *value*, or None when it draws nothing."""
    import svgwriter as svg

    if not isinstance(value, (svg.Document, svg.Element)):
        return None
    try:
        return value._repr_svg_()
    except Exception:  # noqa: BLE001 - a snippet object that cannot be drawn just gets no picture
        return None



def _on_one_canvas(drawn: list[tuple[Any, str]]) -> list[str]:
    """Several loose elements drawn in one shared frame (their joint bounds), so moves and sizes compare.

    Documents, and a single picture, keep their own frame.
    """
    import svgwriter as svg

    if len(drawn) < 2 or not all(isinstance(value, svg.Element) and value.tag != "svg" for value, _ in drawn):
        return [picture for _, picture in drawn]
    try:
        boxes = [value.bounds() for value, _ in drawn]
    except Exception:  # noqa: BLE001 - elements without bounds keep their own frames
        boxes = [None]
    if any(box is None for box in boxes):
        return [picture for _, picture in drawn]
    left, top = min(box.x for box in boxes), min(box.y for box in boxes)
    right, bottom = max(box.x + box.width for box in boxes), max(box.y + box.height for box in boxes)
    pad = max(right - left, bottom - top) * CANVAS_PAD
    width, height = right - left + 2 * pad, bottom - top + 2 * pad
    pictures = []
    for value, _ in drawn:
        doc = svg.Document(width=width, height=height, view_box=(left - pad, top - pad, width, height))
        doc.add(value.clone())
        pictures.append(doc._repr_svg_())
    return pictures


def _inside_shown(value: Any, drawn: list[tuple[Any, str]]) -> bool:
    """Whether *value* is an element inside another drawing shown for the same block (so already visible)."""
    import svgwriter as svg

    if not isinstance(value, svg.Element):
        return False
    root = value.root()
    for other, _ in drawn:
        holder = other.root if isinstance(other, svg.Document) else other
        if other is not value and holder is not value and (holder is root or value in holder.iter()):
            return True
    return False


@contextlib.contextmanager
def _sandbox() -> Iterator[Path]:
    """A scratch working directory with the sample files snippets read."""
    with tempfile.TemporaryDirectory(prefix="snippets-") as work:
        here = Path.cwd()
        (Path(work) / "sketch.excalidraw").write_bytes(SAMPLE.read_bytes())
        os.chdir(work)
        try:
            yield Path(work)
        finally:
            os.chdir(here)


def render_page(page: Path) -> dict[int, list[str]]:
    """The SVGs under each block of *page* that makes, changes or saves drawings, by block index.

    A block that draws several things gets each of them, shown side by side.
    """
    return render_blocks(BLOCK.findall(page.read_text(encoding="utf-8")), page.name)


def doctest_source(text: str) -> str:
    """The code of a doctest block: its ``>>>`` and ``...`` lines without prompts (expected output dropped)."""
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith((">>> ", "... ")) or stripped in (">>>", "..."):
            lines.append(stripped[4:])
    return "\n".join(lines)


def _keeping_shown_values(block: str) -> str:
    """*block* with each top-level bare expression also kept in ``__shown__``, so drawings it shows count."""
    try:
        tree = ast.parse(block)
    except SyntaxError:
        return block
    for position, statement in enumerate(tree.body):
        if isinstance(statement, ast.Expr) and not isinstance(statement.value, ast.Constant):
            keep = ast.Attribute(ast.Name(SHOWN, ast.Load()), "append", ast.Load())
            tree.body[position] = ast.Expr(ast.Call(keep, [statement.value], []))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def render_blocks(blocks: list[str], label: str) -> dict[int, list[str]]:
    """The SVGs under each of *blocks* (run in order in one namespace) that makes, changes or saves drawings.

    Blocks that fail (an optional extra missing, say) get no picture; the snippet tests report failures.
    """
    namespace: dict[str, Any] = {"__name__": "__docs__"}
    shown: dict[int, list[str]] = {}
    last: dict[int, str] = {}
    with _sandbox(), warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        for index, block in enumerate(blocks):
            namespace[SHOWN] = []
            try:
                exec(compile(_keeping_shown_values(block), f"{label}[{index}]", "exec"), namespace)
            except Exception:  # noqa: BLE001 - see the docstring
                continue
            saves = bool(SAVES.search(block))
            drawn = []
            for value in [*(namespace.get(name) for name in reversed(_names(block))), *namespace[SHOWN]]:
                picture = _picture(value)
                if picture is not None and all(picture != seen for _, seen in drawn) and \
                        (saves or last.get(id(value)) != picture):
                    last[id(value)] = picture
                    drawn.append((value, picture))
            kept = [(value, picture) for value, picture in drawn if not _inside_shown(value, drawn)]
            if kept:
                shown[index] = _on_one_canvas(kept[-MAX_PICTURES:])
    return shown


def image_name(page: Path, index: int, number: int = 0) -> str:
    """The file name of picture *number* of block *index* on *page*."""
    slug = page.relative_to(DOCS).with_suffix("").as_posix().replace("/", "-")
    return f"{slug}-{index}-{number}.svg"


def write_images(out: Path = OUTPUT) -> dict[str, dict[int, list[str]]]:
    """Render every page's pictures into *out*; returns the file of each block, by page (relative to docs)."""
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.svg"):
        old.unlink()
    found: dict[str, dict[int, list[str]]] = {}
    for page in pages():
        for index, pictures in render_page(page).items():
            names = []
            for number, picture in enumerate(pictures):
                name = image_name(page, index, number)
                (out / name).write_text(picture, encoding="utf-8")
                names.append(name)
            found.setdefault(page.relative_to(DOCS).with_suffix("").as_posix(), {})[index] = names
    return found
