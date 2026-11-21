"""
The standard derived palette entries and role styles shared by every built-in theme.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ._constants import BORDER_MIX, LINE_WIDTH, MUTED_MIX, SHADOW_ALPHA, THIN_LINE_WIDTH

if TYPE_CHECKING:
    from .theme import Theme

__all__ = ["DERIVED_PALETTE", "STANDARD_ROLES"]


DERIVED_PALETTE: dict[str, str] = {
    "border": f"=mix({{palette.foreground}}, {{palette.background}}, {BORDER_MIX})",
    "muted": f"=mix({{palette.foreground}}, {{palette.background}}, {MUTED_MIX})",
    "shadow": f"=alpha({{palette.foreground}}, {SHADOW_ALPHA})",
    "on_primary": "=readable({palette.primary}, {palette.background}, {palette.foreground})",
}


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
    "shadow": _fill("{palette.shadow}"),
    "outline": _stroke("{palette.border}", THIN_LINE_WIDTH),
    "line": _stroke("{palette.primary}"),
    "grid": _stroke("{palette.border}", THIN_LINE_WIDTH),
    "dot": {"fill": "{palette.accent}", "stroke": "{palette.primary}", "stroke-width": THIN_LINE_WIDTH},
    "pattern": _fill("{palette.primary}"),
    "filter.shadow": {"flood-color": "{palette.shadow}"},
    "filter.ink": {"flood-color": "{palette.foreground}"},
    "arrow.line": _stroke("{palette.foreground}"),
    "arrow.head": _fill("{palette.foreground}"),
    "text": _text("{palette.foreground}", "text"),
    "title": _text("{palette.primary}", "title", "bold"),
    "subtitle": _text("{palette.muted}", "subtitle"),
    "caption": _text("{palette.muted}", "caption"),
    "code": _text("{palette.foreground}", "text", family="{fonts.monospace}"),
    "label": _text("{palette.on_primary}", "text", "bold"),
    "success": _fill("{palette.success}"),
    "warning": _fill("{palette.warning}"),
    "error": _fill("{palette.error}"),
}
