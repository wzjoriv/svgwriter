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

    Blocks that fail (an optional extra missing, say) get no picture; the snippet tests report failures.
    """
    namespace: dict[str, Any] = {"__name__": "__docs__"}
    shown: dict[int, list[str]] = {}
    last: dict[int, str] = {}
    with _sandbox(), warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        for index, block in enumerate(BLOCK.findall(page.read_text(encoding="utf-8"))):
            try:
                exec(compile(block, f"{page.name}[{index}]", "exec"), namespace)
            except Exception:  # noqa: BLE001 - see the docstring
                continue
            saves = bool(SAVES.search(block))
            drawn = []
            for name in reversed(_names(block)):
                value = namespace.get(name)
                picture = _picture(value)
                if picture is not None and all(picture != seen for _, seen in drawn) and \
                        (saves or last.get(id(value)) != picture):
                    last[id(value)] = picture
                    drawn.append((value, picture))
            pictures = [picture for value, picture in drawn if not _inside_shown(value, drawn)]
            if pictures:
                shown[index] = pictures[-MAX_PICTURES:]
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
