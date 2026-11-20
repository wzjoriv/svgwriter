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
from typing import TYPE_CHECKING, Any

from .._registry import register_importer
from ._constants import (
    DISPLAY_SCALE,
    DOT,
    DVISVGM,
    ENGINES,
    INSTALL_HINT,
    LATEX,
    LATEX_TEMPLATE,
    MATHTEXT_SIZE,
    MERMAID,
    MERMAID_CONFIG,
    MPL_CLOSE,
    MPL_CURVE3,
    MPL_CURVE4,
    MPL_LINETO,
    MPL_MOVETO,
    TIMEOUT_SECONDS,
    ZIAMATH_SIZE,
)

if TYPE_CHECKING:
    from ...document import Document
    from ...elements.structure import Group

__all__ = ["DiagramToolError", "latex", "read_d2", "read_dot", "read_mermaid", "read_plantuml"]


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
    executable = _tool(MERMAID)
    with tempfile.TemporaryDirectory() as folder:
        source, target, config = (Path(folder) / name for name in ("in.mmd", "out.svg", "config.json"))
        source.write_bytes(data)
        config.write_text(json.dumps(MERMAID_CONFIG), encoding="utf-8")
        _run([executable, "-i", str(source), "-o", str(target), "-t", theme, "-c", str(config), "-q"])
        return _document(target.read_bytes())


def latex(source: str, *, display: bool = False, preamble: str = "", engine: str = "auto") -> Group:
    r"""A LaTeX formula or snippet as vector outlines.

    With ``engine="auto"`` the first available engine typesets it: real TeX
    (``latex`` + ``dvisvgm``, exact and with every package), then Ziamath
    (pure Python, the ``pysvgwriter[math]`` extra), then matplotlib's mathtext.

    Parameters
    ----------
    source : str
        Math without delimiters (``r"e^{i\pi} + 1 = 0"``), or any LaTeX body
        when it already contains ``$`` or ``\begin``.
    display : bool, optional
        Typeset math in display style. Defaults to False.
    preamble : str, optional
        Extra preamble lines (``\usepackage{...}``), TeX only. Defaults to "".
    engine : {"auto", "tex", "ziamath", "mathtext"}, optional
        Which typesetter to use. Defaults to "auto".

    Returns
    -------
    Group
        The glyph outlines (no fonts needed), in points with the baseline
        near y = 0; place it with ``place`` or ``align``.

    Raises
    ------
    DiagramToolError
        If ``latex`` or ``dvisvgm`` is missing or the source does not compile.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # formula = svg.latex(r"\int_0^1 x^2\,dx = \frac{1}{3}").place(50, 20)
    """
    from ...elements.structure import Group

    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}; use one of {', '.join(ENGINES)}")
    has_tex = bool((os.environ.get("SVGWRITER_LATEX") or shutil.which(LATEX))
                   and (os.environ.get("SVGWRITER_DVISVGM") or shutil.which(DVISVGM)))
    if engine in ("ziamath", "mathtext") or (engine == "auto" and not has_tex):
        for name, typeset in (("ziamath", _ziamath), ("mathtext", _mathtext)):
            if engine in (name, "auto"):
                result = typeset(source, display)
                if result is not None:
                    return result
        if engine != "auto":
            raise DiagramToolError(f"the {engine} engine is not installed; pip install "
                                   f"{'ziamath' if engine == 'ziamath' else 'matplotlib'}")
    body = source if ("$" in source or r"\begin" in source) else (
        rf"$\displaystyle {source}$" if display else f"${source}$")
    latex_tool, svg_tool = _tool(LATEX), _tool(DVISVGM)
    with tempfile.TemporaryDirectory() as folder:
        tex = Path(folder) / "formula.tex"
        text = LATEX_TEMPLATE.format(body=body)
        if preamble:
            text = text.replace(r"\begin{document}", preamble + "\n" + r"\begin{document}", 1)
        tex.write_text(text, encoding="utf-8")
        _run([latex_tool, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={folder}", str(tex)])
        output = _run([svg_tool, "--no-fonts", "--exact-bbox", "--stdout", str(tex.with_suffix(".dvi"))])
    drawing = _document(output)
    group = Group()
    for element in list(drawing.root):
        if element.tag not in ("title", "desc", "metadata"):
            drawing.root.remove(element)
            group.add(element)
    return group


def _ziamath(source: str, display: bool) -> Group | None:
    """The formula through Ziamath (pure Python, STIX math font) as outlines, or None without Ziamath."""
    try:
        import ziamath
    except ImportError:
        return None
    from ...elements.structure import Group
    from ...io.parser import parse

    if "$" in source:
        rendered = ziamath.Latex(source, size=ZIAMATH_SIZE).svg()
    else:
        rendered = ziamath.Math.fromlatex(source, size=ZIAMATH_SIZE,
                                          mathstyle="display" if display else "text").svg()
    root = parse(rendered)
    group = Group()
    for element in list(root.iter()):
        if element.tag == "use":
            path = element.to_path()
            path.set("fill", element.get("fill") or "black")
            group.add(path)
        elif element.tag in ("rect", "path", "line", "polygon") and not any(
                ancestor.tag == "symbol" for ancestor in _ancestors(element)):
            group.add(element.clone())
    return group


def _ancestors(element: Any) -> list[Any]:
    chain, node = [], element.parent
    while node is not None:
        chain.append(node)
        node = node.parent
    return chain


def _mathtext(source: str, display: bool) -> Group | None:
    """The formula through matplotlib's mathtext (no TeX needed; a large subset of TeX math), or None."""
    try:
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextPath
    except ImportError:
        return None
    from ...elements.shapes import Path
    from ...elements.structure import Group
    from ...pathdata.builder import PathBuilder

    text = source if "$" in source else f"${source}$"
    try:
        outline = TextPath((0, 0), text, size=MATHTEXT_SIZE * (DISPLAY_SCALE if display else 1.0),
                           prop=FontProperties(math_fontfamily="cm"))
    except ValueError as error:
        raise DiagramToolError(f"mathtext could not typeset {source!r}: {error}") from error
    builder = PathBuilder()
    vertices, codes = outline.vertices, outline.codes
    index = 0
    while index < len(codes):
        code = codes[index]
        x, y = float(vertices[index][0]), -float(vertices[index][1])
        if code == MPL_MOVETO:
            builder.move_to(x, y)
        elif code == MPL_LINETO:
            builder.line_to(x, y)
        elif code == MPL_CURVE3:
            end = vertices[index + 1]
            builder.quad_to(x, y, float(end[0]), -float(end[1]))
            index += 1
        elif code == MPL_CURVE4:
            second, end = vertices[index + 1], vertices[index + 2]
            builder.curve_to(x, y, float(second[0]), -float(second[1]), float(end[0]), -float(end[1]))
            index += 2
        elif code == MPL_CLOSE:
            builder.close()
        index += 1
    return Group(Path(builder.build()))


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
    return _document(_run([_tool("plantuml"), "-tsvg", "-pipe"], data))


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
    executable = _tool("d2")
    with tempfile.TemporaryDirectory() as folder:
        source, target = Path(folder) / "in.d2", Path(folder) / "out.svg"
        source.write_bytes(data)
        _run([executable, str(source), str(target)])
        return _document(target.read_bytes())
