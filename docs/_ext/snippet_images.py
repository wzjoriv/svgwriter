"""
Sphinx extension: under each Python block or docstring example that draws something, the picture it draws.

The pictures come from ``scripts/svgwriter_tools/_snippets.py``: guide pages' blocks are run once when the build
starts, and each documented object's examples (``>>>`` blocks) when its page is read.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from docutils import nodes
from sphinx import addnodes

ROOT = Path(__file__).resolve().parents[2]
FOLDER = "_snippets"
ALT = "What the code above draws"
_TOOL: list[ModuleType] = []


def _tool() -> ModuleType:
    """The snippet renderer, loaded by path so the docs build needs none of the developer tools' dependencies."""
    if not _TOOL:
        path = ROOT / "scripts" / "svgwriter_tools" / "_snippets.py"
        spec = importlib.util.spec_from_file_location("_svgwriter_snippets", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _TOOL.append(module)
    return _TOOL[0]


def _render(app: Any) -> None:
    app.env.snippet_images = _tool().write_images(Path(app.srcdir) / FOLDER)


def _figure(names: list[str]) -> Any:
    figure = nodes.figure(classes=["snippet-result"])
    for name in names:
        figure += nodes.image(uri=f"/{FOLDER}/{name}", alt=ALT)
    return figure


def _after(block: Any, figure: Any) -> None:
    block.parent.insert(block.parent.index(block) + 1, figure)


def _guide_blocks(app: Any, doctree: Any) -> None:
    found = getattr(app.env, "snippet_images", {}).get(app.env.docname, {})
    blocks = [node for node in doctree.findall(nodes.literal_block) if node.get("language") == "python"]
    for index, block in enumerate(blocks):
        if found.get(index):
            _after(block, _figure(found[index]))


def _docstring_examples(app: Any, doctree: Any) -> None:
    """Each documented object's ``>>>`` examples, run together, with pictures under those that draw."""
    tool = _tool()
    groups: dict[int, list[Any]] = {}
    for block in doctree.findall(nodes.doctest_block):
        owner = next((node for node in _ancestors(block) if isinstance(node, addnodes.desc)), None)
        groups.setdefault(id(owner), []).append(block)
    out = Path(app.srcdir) / FOLDER
    out.mkdir(parents=True, exist_ok=True)
    slug = app.env.docname.replace("/", "-")
    for number, blocks in enumerate(groups.values()):
        sources = [tool.doctest_source(block.astext()) for block in blocks]
        for index, pictures in tool.render_blocks(sources, app.env.docname).items():
            names = []
            for count, picture in enumerate(pictures):
                name = f"api-{slug}-{number}-{index}-{count}.svg"
                (out / name).write_text(picture, encoding="utf-8")
                names.append(name)
            _after(blocks[index], _figure(names))


def _ancestors(node: Any) -> Any:
    while node is not None:
        node = node.parent
        yield node


def _attach(app: Any, doctree: Any) -> None:
    _guide_blocks(app, doctree)
    _docstring_examples(app, doctree)


def setup(app: Any) -> dict[str, Any]:
    app.connect("builder-inited", _render)
    app.connect("doctree-read", _attach, priority=400)
    return {"parallel_read_safe": False, "env_version": 2}
