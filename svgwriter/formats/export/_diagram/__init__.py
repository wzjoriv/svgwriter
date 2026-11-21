"""
Diagram languages in: Graphviz DOT and Mermaid, drawn by their own command-line tools.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ...._internal._constants import DOT, MERMAID
from ...._internal._tools import find_tool, run_tool, svg_document
from .._registry import register_importer
from ._constants import MERMAID_CONFIG

if TYPE_CHECKING:
    from ....document import Document

__all__ = ["read_d2", "read_dot", "read_mermaid", "read_plantuml"]


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
    executable = find_tool(DOT)
    if engine != DOT:
        executable = str(Path(executable).with_name(Path(executable).name.replace(DOT, engine, 1)))
    return svg_document(run_tool([executable, "-Tsvg"], data))


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
    convert like any other text. Without ``mmdc``, flowcharts (``graph`` /
    ``flowchart``) are parsed and laid out by svgwriter itself; other
    diagram kinds need the CLI.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # doc = svg.Document.open("flow.mmd"); doc.save("flow.png")
    """
    if not (os.environ.get("SVGWRITER_MMDC") or shutil.which(MERMAID)):
        from ._mermaid import flowchart_document

        try:
            return flowchart_document(data.decode("utf-8-sig"))
        except ValueError:
            pass
    executable = find_tool(MERMAID)
    with tempfile.TemporaryDirectory() as folder:
        source, target, config = (Path(folder) / name for name in ("in.mmd", "out.svg", "config.json"))
        source.write_bytes(data)
        config.write_text(json.dumps(MERMAID_CONFIG), encoding="utf-8")
        run_tool([executable, "-i", str(source), "-o", str(target), "-t", theme, "-c", str(config), "-q"])
        return svg_document(target.read_bytes())


@register_importer("plantuml", extensions=(".puml", ".plantuml"))
def read_plantuml(data: bytes) -> Document:
    """A PlantUML diagram drawn by PlantUML (``plantuml -tsvg -pipe``), as a document.

    Parameters
    ----------
    data : bytes
        PlantUML source.

    Returns
    -------
    Document
        The drawing as native SVG elements.

    Raises
    ------
    DiagramToolError
        If ``plantuml`` is missing or rejects the diagram.
    """
    return svg_document(run_tool([find_tool("plantuml"), "-tsvg", "-pipe"], data))


@register_importer("d2", extensions=(".d2",))
def read_d2(data: bytes) -> Document:
    """A D2 diagram drawn by D2, as a document.

    Parameters
    ----------
    data : bytes
        D2 source.

    Returns
    -------
    Document
        The drawing as native SVG elements.

    Raises
    ------
    DiagramToolError
        If ``d2`` is missing or rejects the diagram.
    """
    executable = find_tool("d2")
    with tempfile.TemporaryDirectory() as folder:
        source, target = Path(folder) / "in.d2", Path(folder) / "out.svg"
        source.write_bytes(data)
        run_tool([executable, str(source), str(target)])
        return svg_document(target.read_bytes())
