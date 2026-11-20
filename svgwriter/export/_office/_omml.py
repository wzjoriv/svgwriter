"""
LaTeX to Office Math (OMML), through MathML from ``latex2mathml``, for editable equations in PowerPoint and Word.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from . import require
from ._constants import BAR_CHARS, GROUP_CHARS, M_NS, MATHML_NS, NARY_CHARS

__all__ = ["latex_to_omml"]


def latex_to_omml(source: str, run_properties: str = "") -> str:
    r"""A ``<m:oMathPara>`` element (as XML text) for the LaTeX math *source*.

    Parameters
    ----------
    source : str
        Math without delimiters, or wrapped in ``$...$``.
    run_properties : str, optional
        XML inserted in every run after ``<m:rPr>``, such as an ``<a:rPr>``
        or ``<w:rPr>`` with the font and size; it must declare its own
        namespace. Defaults to "".

    Returns
    -------
    str
        The equation, with the ``m`` namespace declared on the root.

    Raises
    ------
    ValueError
        If the source cannot be parsed or uses MathML this converter does not map.
    OfficeExtraError
        If ``latex2mathml`` is not installed.

    Notes
    -----
    Maps ``mi mn mo mtext mrow mstyle mfrac msup msub msubsup msqrt mroot
    munder mover munderover mtable`` and ``\left``/``\right`` fences onto
    runs, fractions, scripts, radicals, n-ary operators (sums, integrals),
    accents, bars, limits, matrices and delimiters.

    Examples
    --------
    >>> from svgwriter.export._office._omml import latex_to_omml
    >>> xml = latex_to_omml(r"\frac{a}{b}")
    >>> "<m:f>" in xml and xml.startswith("<m:oMathPara")
    True
    """
    converter = require("latex2mathml.converter")
    text = source.strip()
    if len(text) > 1 and text.startswith("$") and text.endswith("$"):
        text = text.strip("$")
    try:
        mathml = converter.convert(text)
    except Exception as error:
        raise ValueError(f"cannot read {source!r} as LaTeX math: {error}") from error
    try:
        body = _Writer(run_properties).row(list(ElementTree.fromstring(mathml)))
    except IndexError as error:
        raise ValueError(f"incomplete LaTeX math in {source!r}") from error
    return f'<m:oMathPara xmlns:m="{M_NS}"><m:oMath>{body}</m:oMath></m:oMathPara>'


def _name(node: Any) -> str:
    return node.tag.removeprefix(f"{{{MATHML_NS}}}")


def _text(node: Any) -> str:
    return "".join(node.itertext())


def _single_mo(node: Any) -> str | None:
    """The character of a lone ``<mo>``, also inside a one-child ``<mrow>``, or None."""
    while _name(node) == "mrow" and len(node) == 1:
        node = node[0]
    return _text(node) if _name(node) == "mo" else None


class _Writer:
    """Converts MathML nodes to OMML text with the given run properties."""

    def __init__(self, run_properties: str) -> None:
        self.run_properties = run_properties

    def row(self, nodes: list[Any]) -> str:
        parts, index = [], 0
        while index < len(nodes):
            node = nodes[index]
            if self._nary_base(node) is not None:
                body = self.node(nodes[index + 1]) if index + 1 < len(nodes) else ""
                parts.append(self._nary(node, body))
                index += 2
                continue
            parts.append(self.node(node))
            index += 1
        return "".join(parts)

    def node(self, node: Any) -> str:
        name = _name(node)
        children = list(node)
        if name in ("math", "mstyle", "mpadded", "menclose", "semantics"):
            return self.row(children)
        if name == "mrow":
            return self._fenced(children) or self.row(children)
        if name in ("mi", "mn", "mo", "mtext", "ms"):
            return self._run(node)
        if name in ("mspace", "mphantom", "annotation", "none"):
            return ""
        if name == "mfrac":
            bar = '<m:fPr><m:type m:val="noBar"/></m:fPr>' if node.get("linethickness") in ("0", "0pt") else ""
            return f"<m:f>{bar}<m:num>{self.node(children[0])}</m:num><m:den>{self.node(children[1])}</m:den></m:f>"
        if name == "msup":
            return f"<m:sSup>{self._e(children[0])}<m:sup>{self.node(children[1])}</m:sup></m:sSup>"
        if name == "msub":
            if len(_single_mo(children[0]) or "") > 1:
                return f"<m:limLow>{self._e(children[0])}<m:lim>{self.node(children[1])}</m:lim></m:limLow>"
            return f"<m:sSub>{self._e(children[0])}<m:sub>{self.node(children[1])}</m:sub></m:sSub>"
        if name == "msubsup":
            return (f"<m:sSubSup>{self._e(children[0])}<m:sub>{self.node(children[1])}</m:sub>"
                    f"<m:sup>{self.node(children[2])}</m:sup></m:sSubSup>")
        if name == "msqrt":
            return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/>{self._e_row(children)}</m:rad>'
        if name == "mroot":
            return f"<m:rad><m:deg>{self.node(children[1])}</m:deg>{self._e(children[0])}</m:rad>"
        if name in ("mover", "munder"):
            return self._under_over(name, children)
        if name == "munderover":
            inner = f"<m:limLow>{self._e(children[0])}<m:lim>{self.node(children[1])}</m:lim></m:limLow>"
            return f"<m:limUpp><m:e>{inner}</m:e><m:lim>{self.node(children[2])}</m:lim></m:limUpp>"
        if name == "mtable":
            rows = "".join("<m:mr>" + "".join(self._e_row(list(cell)) for cell in row) + "</m:mr>"
                           for row in children if _name(row) in ("mtr", "mlabeledtr"))
            return f"<m:m>{rows}</m:m>"
        raise ValueError(f"MathML <{name}> has no Office equation equivalent here")

    def _e(self, node: Any) -> str:
        return f"<m:e>{self.node(node)}</m:e>"

    def _e_row(self, nodes: list[Any]) -> str:
        return f"<m:e>{self.row(nodes)}</m:e>"

    def _run(self, node: Any) -> str:
        text = _text(node)
        if not text:
            return ""
        name = _name(node)
        style = ""
        if name in ("mtext", "ms"):
            style = "<m:rPr><m:nor/></m:rPr>"
        elif node.get("mathvariant") == "normal" or (name == "mi" and len(text) > 1) or name == "mo" and len(text) > 1:
            style = '<m:rPr><m:sty m:val="p"/></m:rPr>'
        return f'<m:r>{style}{self.run_properties}<m:t xml:space="preserve">{escape(text)}</m:t></m:r>'

    def _fenced(self, children: list[Any]) -> str | None:
        """A ``\\left ... \\right`` row as an ``<m:d>`` delimiter, or None."""
        if len(children) < 2 or not all(_name(c) == "mo" and c.get("fence") == "true"
                                        for c in (children[0], children[-1])):
            return None
        begin, end = _text(children[0]), _text(children[-1])
        return (f"<m:d><m:dPr><m:begChr m:val={quoteattr(begin)}/><m:endChr m:val={quoteattr(end)}/></m:dPr>"
                f"{self._e_row(children[1:-1])}</m:d>")

    def _nary_base(self, node: Any) -> str | None:
        """The operator of a scripted n-ary symbol (sum, integral, ...), or None."""
        if _name(node) not in ("msub", "msup", "msubsup", "munder", "mover", "munderover") and _name(node) != "mo":
            return None
        base = node if _name(node) == "mo" else node[0]
        symbol = _single_mo(base)
        return symbol if symbol in NARY_CHARS else None

    def _nary(self, node: Any, body: str) -> str:
        name, children = _name(node), list(node)
        lower = upper = None
        if name in ("msub", "munder", "msubsup", "munderover"):
            lower = self.node(children[1])
        if name in ("msup", "mover"):
            upper = self.node(children[1])
        elif name in ("msubsup", "munderover"):
            upper = self.node(children[2])
        location = "undOvr" if name.startswith("mu") else "subSup"
        hide = ('<m:subHide m:val="1"/>' if lower is None else "") + ('<m:supHide m:val="1"/>' if upper is None else "")
        return (f"<m:nary><m:naryPr><m:chr m:val={quoteattr(self._nary_base(node) or '')}/>"
                f'<m:limLoc m:val="{location}"/>{hide}</m:naryPr><m:sub>{lower or ""}</m:sub>'
                f"<m:sup>{upper or ''}</m:sup><m:e>{body}</m:e></m:nary>")

    def _under_over(self, name: str, children: list[Any]) -> str:
        mark = _single_mo(children[1])
        position = "top" if name == "mover" else "bot"
        if mark in BAR_CHARS:
            return f'<m:bar><m:barPr><m:pos m:val="{position}"/></m:barPr>{self._e(children[0])}</m:bar>'
        if mark in GROUP_CHARS:
            return (f"<m:groupChr><m:groupChrPr><m:chr m:val={quoteattr(mark or '')}/>"
                    f'<m:pos m:val="{position}"/></m:groupChrPr>{self._e(children[0])}</m:groupChr>')
        if name == "mover" and mark is not None and len(mark) == 1:
            return f"<m:acc><m:accPr><m:chr m:val={quoteattr(mark)}/></m:accPr>{self._e(children[0])}</m:acc>"
        tag = "limUpp" if name == "mover" else "limLow"
        return f"<m:{tag}>{self._e(children[0])}<m:lim>{self.node(children[1])}</m:lim></m:{tag}>"
