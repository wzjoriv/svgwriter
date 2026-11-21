"""
Notebook entries: ``main.ipynb`` written from a ``# %%`` script, and run headlessly for ``svgwriter build``.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..._internal._platform import missing
from ._config import ProjectConfig, ProjectError
from ._constants import (
    CELL_MARKER,
    HEADLESS_ENV,
    KERNEL,
    MAIN_GUARD,
    MARKDOWN_TAG,
    NBFORMAT,
    NBFORMAT_MINOR,
    NOTEBOOK_TIMEOUT,
    PREVIEW_CELLS,
)

__all__ = ["headless", "kernel_object", "notebook_of", "run_notebook"]


def _cells(text: str) -> list[tuple[str, str]]:
    """``(kind, source)`` cells: the module docstring and ``# %% [markdown]`` blocks as markdown, ``# %%`` blocks as code."""
    tree = ast.parse(text)
    first = tree.body[0] if tree.body else None
    cells: list[tuple[str, str]] = []
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        cells.append(("markdown", (ast.get_docstring(tree) or "").strip()))
        text = "".join(text.splitlines(keepends=True)[first.end_lineno:])
    kind, block = "code", []
    for line in [*text.splitlines(keepends=True), CELL_MARKER]:
        if line.startswith(CELL_MARKER):
            if kind == "markdown":
                body = "\n".join(row.rstrip("\n").removeprefix("#").removeprefix(" ") for row in block).strip("\n")
            else:
                body = "".join(block).strip("\n")
            if body.strip() and MAIN_GUARD not in body:
                cells.append((kind, body))
            kind, block = ("markdown" if line[len(CELL_MARKER):].strip().startswith(MARKDOWN_TAG) else "code"), []
        else:
            block.append(line)
    return cells


def notebook_of(script: str) -> dict[str, Any]:
    """An nbformat 4 notebook from a ``# %%`` script, ending with cells that preview and build the project."""
    cells = []
    for index, (kind, source) in enumerate([*_cells(script), *PREVIEW_CELLS]):
        cell: dict[str, Any] = {"cell_type": kind, "id": f"cell-{index}", "metadata": {}, "source": source}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": KERNEL},
                         "language_info": {"name": "python"}},
            "nbformat": NBFORMAT, "nbformat_minor": NBFORMAT_MINOR}


def headless() -> bool:
    """Whether this kernel is running a project notebook for ``svgwriter build``."""
    return bool(os.environ.get(HEADLESS_ENV))


def kernel_object(name: str) -> object | None:
    """The notebook's own *name* when called from inside a Jupyter kernel that defines it, else None."""
    main = sys.modules.get("__main__")
    if "ipykernel" not in sys.modules or main is None:
        return None
    return getattr(main, name, None)


def run_notebook(config: ProjectConfig, notebook: Path, formats: Sequence[str]) -> list[Path]:
    """Execute *notebook* in a fresh kernel and build the outputs there with its own entry object."""
    try:
        import nbformat
        from nbclient import NotebookClient
        from nbclient.exceptions import CellExecutionError
    except ImportError:
        raise missing("notebook", f"{config.source}: running {notebook.name}", ProjectError) from None
    if not notebook.is_file():
        raise ProjectError(f"{config.source}: project.entry {config.entry!r}: no notebook {notebook.name} in {config.root}")
    document = nbformat.read(notebook, as_version=NBFORMAT)
    document.cells.append(nbformat.v4.new_code_cell(
        "import json as _json, os as _os, svgwriter as _svgwriter\n"
        f"_os.environ.pop({HEADLESS_ENV!r}, None)\n"
        f"print(_json.dumps([str(p) for p in _svgwriter.Project.load({str(config.root)!r}).build({list(formats)!r})]))"))
    previous = os.environ.get(HEADLESS_ENV)
    os.environ[HEADLESS_ENV] = "1"
    try:
        NotebookClient(document, timeout=NOTEBOOK_TIMEOUT, resources={"metadata": {"path": str(config.root)}}).execute()
    except CellExecutionError as error:
        raise ProjectError(f"{notebook}: a cell failed\n{error}") from None
    finally:
        if previous is None:
            os.environ.pop(HEADLESS_ENV, None)
        else:
            os.environ[HEADLESS_ENV] = previous
    printed = "".join(output.get("text", "") for output in document.cells[-1].outputs if output.output_type == "stream")
    return [Path(path) for path in json.loads(printed.strip().splitlines()[-1])]
