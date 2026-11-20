"""
Constants for the diagram importers: tool names, LaTeX template and Mermaid layout.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "ARROW_LENGTH",
    "ARROW_SPREAD",
    "DIRECTIONS",
    "EDGE_RE",
    "EDGE_STROKE",
    "FONT_SIZE",
    "HEADER_RE",
    "ID_RE",
    "LABEL_BACKGROUND",
    "MARGIN",
    "MERMAID_CONFIG",
    "NODE_FILL",
    "NODE_GAP",
    "NODE_STROKE",
    "PADDING_X",
    "PADDING_Y",
    "RANK_GAP",
    "SHAPES",
    "SUBGRAPH_FILL",
    "SUBGRAPH_STROKE",
    "SWEEPS",
]

MERMAID_CONFIG: Final = {"flowchart": {"htmlLabels": False}, "class": {"htmlLabels": False}}
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
