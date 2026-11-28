"""
Sphinx extension: under each Python block that draws something, the picture it draws.

The pictures come from ``scripts/svgwriter_tools/_snippets.py``, which runs every page's blocks once when the
build starts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from docutils import nodes

ROOT = Path(__file__).resolve().parents[2]
FOLDER = "_snippets"


def _render(app: Any) -> None:
    path = ROOT / "scripts" / "svgwriter_tools" / "_snippets.py"
    spec = importlib.util.spec_from_file_location("_svgwriter_snippets", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    app.env.snippet_images = module.write_images(Path(app.srcdir) / FOLDER)


def _attach(app: Any, doctree: Any) -> None:
    found = getattr(app.env, "snippet_images", {}).get(app.env.docname, {})
    if not found:
        return
    blocks = [node for node in doctree.findall(nodes.literal_block) if node.get("language") == "python"]
    for index, block in enumerate(blocks):
        names = found.get(index)
        if not names:
            continue
        figure = nodes.figure(classes=["snippet-result"])
        for name in names:
            figure += nodes.image(uri=f"/{FOLDER}/{name}", alt="What the code above draws")
        block.parent.insert(block.parent.index(block) + 1, figure)


def setup(app: Any) -> dict[str, Any]:
    app.connect("builder-inited", _render)
    app.connect("doctree-read", _attach, priority=400)
    return {"parallel_read_safe": False, "env_version": 1}
