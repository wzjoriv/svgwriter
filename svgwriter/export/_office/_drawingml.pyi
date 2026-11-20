from typing import Any
from ..._internal._paints import Shading
from ...elements.core import Element
from ...pathdata.data import BBox

__all__ = ["gradient_xml", "line_style", "read_gradient", "read_line_style"]

def gradient_xml(
    shading: Shading,
    box: BBox,
    opacity: float,
) -> str: ...

def line_style(
    line: Any,
    width: float,
    dashes: tuple[float, ...],
    cap: str,
    join: str,
    miter: float,
) -> None: ...

def read_line_style(
    path: Element,
    line: Any,
    width: float,
) -> None: ...

def read_gradient(
    fill: Any,
    left: float,
    top: float,
    width: float,
    height: float,
) -> Element | None: ...
