"""
LaTeX formulas as vector outlines, through TeX, Ziamath or matplotlib mathtext.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._constants import (
    DISPLAY_SCALE,
    DVISVGM,
    ENGINES,
    LATEX,
    LATEX_SIZE,
    LATEX_SOURCE,
    LATEX_TEMPLATE,
    MATHTEXT_SIZE,
    MPL_CLOSE,
    MPL_CURVE3,
    MPL_CURVE4,
    MPL_LINETO,
    MPL_MOVETO,
    TEX_SIZE,
    ZIAMATH_SIZE,
)
from ._platform import available, missing
from ._tools import DiagramToolError, find_tool, run_tool, svg_document

if TYPE_CHECKING:
    from ..model.elements.structure import Group

__all__ = ["latex"]


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
        near y = 0; place it with ``place`` or ``align``. Its ``data-latex``
        and ``data-latex-size`` attributes keep the source and font size, so
        PowerPoint and Word exports can write an editable equation instead.

    Raises
    ------
    DiagramToolError
        If ``latex`` or ``dvisvgm`` is missing or the source does not compile.

    Examples
    --------
    >>> import svgwriter as svg
    >>> # formula = svg.latex(r"\int_0^1 x^2\,dx = \frac{1}{3}").place(50, 20)
    """
    from ..model.elements.structure import Group

    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}; use one of {', '.join(ENGINES)}")
    has_tex = available("latex")
    if engine in ("ziamath", "mathtext") or (engine == "auto" and not has_tex):
        for name, typeset in (("ziamath", _ziamath), ("mathtext", _mathtext)):
            if engine in (name, "auto"):
                result = typeset(source, display)
                if result is not None:
                    size = MATHTEXT_SIZE * (DISPLAY_SCALE if display else 1.0) if name == "mathtext" else ZIAMATH_SIZE
                    return _remember(result, source, size)
        if engine != "auto":
            raise missing("ziamath" if engine == "ziamath" else "matplotlib", f"the {engine} engine",
                          DiagramToolError)
    body = source if ("$" in source or r"\begin" in source) else (
        rf"$\displaystyle {source}$" if display else f"${source}$")
    latex_tool, svg_tool = find_tool(LATEX), find_tool(DVISVGM)
    with tempfile.TemporaryDirectory() as folder:
        tex = Path(folder) / "formula.tex"
        text = LATEX_TEMPLATE.format(body=body)
        if preamble:
            text = text.replace(r"\begin{document}", preamble + "\n" + r"\begin{document}", 1)
        tex.write_text(text, encoding="utf-8")
        run_tool([latex_tool, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={folder}", str(tex)])
        output = run_tool([svg_tool, "--no-fonts", "--exact-bbox", "--stdout", str(tex.with_suffix(".dvi"))])
    drawing = svg_document(output)
    group = Group()
    for element in list(drawing.root):
        if element.tag not in ("title", "desc", "metadata"):
            drawing.root.remove(element)
            group.add(element)
    return _remember(group, source, TEX_SIZE)


def _remember(group: Group, source: str, size: float) -> Group:
    """Record the LaTeX source and its font size on *group*, for exports that write native equations."""
    group.set(LATEX_SOURCE, source)
    group.set(LATEX_SIZE, size)
    return group


def _ziamath(source: str, display: bool) -> Group | None:
    """The formula through Ziamath (pure Python, STIX math font) as outlines, or None without Ziamath."""
    try:
        import ziamath
    except ImportError:
        return None
    from ..formats.io.parser import parse
    from ..model.elements.structure import Group

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
    from ..model.elements.shapes import Path
    from ..model.elements.structure import Group
    from ..model.pathdata.builder import PathBuilder

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
