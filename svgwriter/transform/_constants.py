"""
Constants for ``svgwriter.transform``: defaults, tables and patterns.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "ARITY",
    "EPSILON",
    "FUNCTION_RE",
    "NUMBER_RE",
]

EPSILON: Final = 1e-12

FUNCTION_RE: Final = re.compile(r"(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)")
NUMBER_RE: Final = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
ARITY: Final = {
    "matrix": (6,),
    "translate": (1, 2),
    "scale": (1, 2),
    "rotate": (1, 3),
    "skewX": (1,),
    "skewY": (1,),
}
