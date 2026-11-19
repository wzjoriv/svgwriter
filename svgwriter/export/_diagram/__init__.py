"""
Diagram languages in: Graphviz DOT and Mermaid, drawn by their own command-line tools.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Final

from .._registry import register_importer

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["DiagramToolError", "read_dot", "read_mermaid"]

DOT: Final = "dot"
MERMAID: Final = "mmdc"
TIMEOUT_SECONDS: Final = 60
MERMAID_CONFIG: Final = {"flowchart": {"htmlLabels": False}, "class": {"htmlLabels": False}}
INSTALL_HINT: Final = {
    DOT: "install Graphviz (https://graphviz.org/download/) so that `dot` is on PATH",
    MERMAID: "install the Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`) so that `mmdc` is on PATH",
}


class DiagramToolError(RuntimeError):
    """The diagram tool is missing or rejected the input.

    See Also
    --------
    read_dot, read_mermaid : The importers that run the tools.

    Examples
    --------
    >>> from svgwriter.export._diagram import DiagramToolError
    >>> issubclass(DiagramToolError, RuntimeError)
    True
    """


def _tool(name: str) -> str:
    """The executable for *name*, from ``SVGWRITER_<NAME>`` or ``PATH``."""
    found = os.environ.get(f"SVGWRITER_{name.upper()}") or shutil.which(name)
    if not found:
        raise DiagramToolError(f"`{name}` not found; {INSTALL_HINT[name]}")
    return found


def _run(command: list[str], data: bytes | None = None) -> bytes:
    """Run a tool, returning its standard output or raising with its error text."""
    try:
        done = subprocess.run(command, input=data, capture_output=True, timeout=TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DiagramToolError(f"{Path(command[0]).name} failed: {error}") from error
    if done.returncode != 0:
        message = done.stderr.decode("utf-8", "replace").strip() or f"exit status {done.returncode}"
        raise DiagramToolError(f"{Path(command[0]).name}: {message}")
    return done.stdout


def _document(svg_text: bytes) -> Document:
    from ...document import Document

    return Document.from_string(svg_text.decode("utf-8"))


@register_importer("dot", extensions=(".dot", ".gv"))
def read_dot(data: bytes, *, engine: str = DOT) -> Document:
    """A Graphviz graph laid out and drawn by Graphviz, as a document.

    Parameters
    ----------
    data : bytes
        DOT source.
    engine : str, optional
        Graphviz layout program (``dot``, ``neato``, ``fdp``, ``circo``, ...).
        Defaults to ``"dot"``.

    Returns
    -------
    Document
        The drawing as native SVG elements, ready to edit or export.

    Raises
    ------
    DiagramToolError
        If Graphviz is not installed or rejects the graph.

    Notes
    -----
    The executable comes from ``SVGWRITER_DOT`` or ``PATH``; for another
    engine it is looked up next to it.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # doc = svg.Document.open("graph.dot"); doc.save("graph.pdf")
    """
    executable = _tool(DOT)
    if engine != DOT:
        executable = str(Path(executable).with_name(Path(executable).name.replace(DOT, engine, 1)))
    return _document(_run([executable, "-Tsvg"], data))


@register_importer("mermaid", extensions=(".mmd", ".mermaid"))
def read_mermaid(data: bytes, *, theme: str = "default") -> Document:
    """A Mermaid diagram drawn by the Mermaid CLI, as a document.

    Parameters
    ----------
    data : bytes
        Mermaid source.
    theme : str, optional
        Mermaid theme (``default``, ``neutral``, ``dark``, ``forest``). Defaults to ``"default"``.

    Returns
    -------
    Document
        The drawing as native SVG elements.

    Raises
    ------
    DiagramToolError
        If ``mmdc`` is not installed or rejects the diagram.

    Notes
    -----
    Labels are requested as SVG text rather than HTML, so they render and
    convert like any other text.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # doc = svg.Document.open("flow.mmd"); doc.save("flow.png")
    """
    executable = _tool(MERMAID)
    with tempfile.TemporaryDirectory() as folder:
        source, target, config = (Path(folder) / name for name in ("in.mmd", "out.svg", "config.json"))
        source.write_bytes(data)
        config.write_text(json.dumps(MERMAID_CONFIG), encoding="utf-8")
        _run([executable, "-i", str(source), "-o", str(target), "-t", theme, "-c", str(config), "-q"])
        return _document(target.read_bytes())
