"""
The standard derived palette entries and role styles shared by every built-in theme.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..color.color import Color
from ._constants import BORDER_MIX, LINE_WIDTH, MUTED_MIX, THIN_LINE_WIDTH

if TYPE_CHECKING:
    from .palette import Palette
    from .theme import Theme

__all__ = ["DERIVED_PALETTE", "STANDARD_ROLES"]


def _border(p: Palette) -> Color:
    return p.foreground.mix(p.background, BORDER_MIX)


def _muted(p: Palette) -> Color:
    return p.foreground.mix(p.background, MUTED_MIX)


DERIVED_PALETTE: dict[str, Callable[[Palette], Color]] = {"border": _border, "muted": _muted}


def _text(color: str, size: str, weight: str = "regular", family: str = "{fonts.family}") -> dict[str, object]:
    return {"fill": color, "stroke": "none", "font-family": family,
            "font-size": "{fonts.sizes." + size + "}", "font-weight": "{fonts.weights." + weight + "}"}


def _fill(color: str) -> dict[str, object]:
    return {"fill": color, "stroke": "none"}


def _stroke(color: str, width: float = LINE_WIDTH) -> dict[str, object]:
    return {"fill": "none", "stroke": color, "stroke-width": width}


STANDARD_ROLES: dict[str, dict[str, object] | Callable[[Theme], object]] = {
    "background": _fill("{palette.background}"),
    "surface": _fill("{palette.surface}"),
    "box": {"fill": "{palette.surface}", "stroke": "{palette.border}", "stroke-width": THIN_LINE_WIDTH},
    "shape": _fill("{palette.primary}"),
    "accent": _fill("{palette.accent}"),
    "outline": _stroke("{palette.border}", THIN_LINE_WIDTH),
    "line": _stroke("{palette.foreground}"),
    "grid": _stroke("{palette.border}", THIN_LINE_WIDTH),
    "dot": _fill("{palette.foreground}"),
    "arrow.line": _stroke("{palette.foreground}"),
    "arrow.head": _fill("{palette.foreground}"),
    "text": _text("{palette.foreground}", "text"),
    "title": _text("{palette.foreground}", "title", "bold"),
    "subtitle": _text("{palette.muted}", "subtitle"),
    "caption": _text("{palette.muted}", "caption"),
    "code": _text("{palette.foreground}", "text", family="{fonts.monospace}"),
    "label": _text("{palette.on_primary}", "text", "bold"),
    "success": _fill("{palette.success}"),
    "warning": _fill("{palette.warning}"),
    "error": _fill("{palette.error}"),
}
