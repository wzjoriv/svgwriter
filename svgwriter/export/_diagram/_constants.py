"""
Constants for the diagram importers: tool names, LaTeX template and Mermaid layout.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "ARROW_LENGTH", "ARROW_SPREAD", "DIRECTIONS", "DISPLAY_SCALE", "DOT", "DVISVGM", "EDGE_RE",
    "EDGE_STROKE", "ENGINES", "FONT_SIZE", "HEADER_RE", "ID_RE", "INSTALL_HINT", "LABEL_BACKGROUND", "LATEX",
    "LATEX_TEMPLATE", "MARGIN", "MATHTEXT_SIZE", "MERMAID", "MERMAID_CONFIG", "MPL_CLOSE", "MPL_CURVE3",
    "MPL_CURVE4", "MPL_LINETO", "MPL_MOVETO", "NODE_FILL", "NODE_GAP", "NODE_STROKE", "PADDING_X",
    "PADDING_Y", "RANK_GAP", "SHAPES", "SUBGRAPH_FILL", "SUBGRAPH_STROKE", "SWEEPS", "TIMEOUT_SECONDS",
    "ZIAMATH_SIZE"
]

DOT: Final = "dot"
MERMAID: Final = "mmdc"
TIMEOUT_SECONDS: Final = 60
MERMAID_CONFIG: Final = {"flowchart": {"htmlLabels": False}, "class": {"htmlLabels": False}}
LATEX_TEMPLATE: Final = (r"\documentclass[preview,border=0pt]{{standalone}}" "\n"
                         r"\usepackage{{amsmath,amssymb}}" "\n"
                         r"\begin{{document}}" "\n{body}\n" r"\end{{document}}" "\n")
LATEX: Final = "latex"
DVISVGM: Final = "dvisvgm"
INSTALL_HINT: Final = {
    DOT: "install Graphviz (https://graphviz.org/download/) so that `dot` is on PATH",
    MERMAID: "install the Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`) so that `mmdc` is on PATH",
    LATEX: "install a TeX distribution (TeX Live or MiKTeX) so that `latex` is on PATH",
    DVISVGM: "install dvisvgm (bundled with TeX Live and MiKTeX) so that `dvisvgm` is on PATH",
    "plantuml": "install PlantUML so that `plantuml` is on PATH",
    "d2": "install D2 (https://d2lang.com) so that `d2` is on PATH",
}
ENGINES: Final = ("auto", "tex", "ziamath", "mathtext")
ZIAMATH_SIZE: Final = 10.0
MATHTEXT_SIZE: Final = 10.0
DISPLAY_SCALE: Final = 1.2
MPL_MOVETO: Final = 1
MPL_LINETO: Final = 2
MPL_CURVE3: Final = 3
MPL_CURVE4: Final = 4
MPL_CLOSE: Final = 79
FONT_SIZE: Final = 14.0
PADDING_X: Final = 14.0
PADDING_Y: Final = 9.0
RANK_GAP: Final = 50.0
NODE_GAP: Final = 30.0
MARGIN: Final = 10.0
SWEEPS: Final = 6
ARROW_LENGTH: Final = 8.0
ARROW_SPREAD: Final = 28.0
NODE_FILL: Final = "#ececff"
NODE_STROKE: Final = "#9370db"
EDGE_STROKE: Final = "#333333"
SUBGRAPH_FILL: Final = "#ffffde"
SUBGRAPH_STROKE: Final = "#aaaa33"
LABEL_BACKGROUND: Final = "#e8e8e8"
DIRECTIONS: Final = {"TD": "TB", "TB": "TB", "BT": "BT", "LR": "LR", "RL": "RL"}
SHAPES: Final = [  # (opening, closing, shape) tried longest first
    ("(((", ")))", "double-circle"), ("([", "])", "stadium"), ("[[", "]]", "subroutine"), ("[(", ")]", "cylinder"),
    ("((", "))", "circle"), ("{{", "}}", "hexagon"), ("[/", "/]", "parallelogram"), ("[\\", "\\]", "parallelogram-alt"),
    ("[/", "\\]", "trapezoid"), ("[\\", "/]", "trapezoid-alt"), (">", "]", "flag"), ("{", "}", "diamond"),
    ("(", ")", "round"), ("[", "]", "rect"),
]
HEADER_RE: Final = re.compile(r"^\s*(?:graph|flowchart)\s*(TD|TB|BT|LR|RL)?\s*$", re.I)
EDGE_RE: Final = re.compile(
    r"\s*(?P<arrow><-->|<==>|-\.->|-\.-|==>|===|-->|---|--o|--x|~~~)\s*(?:\|(?P<label>[^|]*)\|)?\s*"
    r"|\s*--\s*(?P<label2>[^->]+?)\s*-->\s*|\s*==\s*(?P<label3>[^=>]+?)\s*==>\s*|\s*-\.\s*(?P<label4>.+?)\s*\.->\s*")
ID_RE: Final = re.compile(r"[A-Za-z0-9_][\w\-]*")
