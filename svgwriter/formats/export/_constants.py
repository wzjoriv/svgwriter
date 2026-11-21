"""
Constants for the export package's shared helpers: flattening, text, HTML and SVG.
"""

from __future__ import annotations

import re
from typing import Final

from ...model.attributes.length import Unit

__all__ = [
    "PHYSICAL_UNITS",
    "BODY_SIZE",
    "BOLD_RE",
    "BULLET",
    "BULLET_RE",
    "CODE_FILL",
    "GZIP_MAGIC",
    "HEADING_RE",
    "HEADING_SIZES",
    "INDENT_PER_LEVEL",
    "INLINE_RE",
    "LINE_HEIGHT",
    "MARGIN",
    "MONOSPACE",
    "NUMBERED_RE",
    "PAGE",
    "SANS",
    "SCRIPT",
    "SPACES_PER_LEVEL",
    "SVG_RE",
]

SVG_RE: Final = re.compile(r"<svg[\s>].*?</svg\s*>", re.S | re.I)
PAGE: Final = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ margin: 0; background: {background}; display: flex; justify-content: center; align-items: center;
  min-height: 100vh; }}
svg {{ max-width: 100vw; max-height: 100vh; height: auto; }}
{css}
</style>
</head>
<body>
{svg}
{script}</body>
</html>
"""
SCRIPT: Final = """<script>
const svgwriterHandlers = {handlers};
for (const [id, events] of Object.entries(svgwriterHandlers)) {{
  const element = document.getElementById(id);
  if (!element) continue;
  element.style.cursor = "pointer";
  for (const [event, code] of Object.entries(events)) {{
    element.addEventListener(event, new Function("event", code));
  }}
}}
</script>
"""
GZIP_MAGIC: Final = b"\x1f\x8b"
BODY_SIZE: Final = 16.0
LINE_HEIGHT: Final = 1.4
MARGIN: Final = 10.0
HEADING_SIZES: Final = {1: 32.0, 2: 26.0, 3: 22.0, 4: 19.0, 5: 17.0, 6: 16.0}
BULLET: Final = "• "
MONOSPACE: Final = "monospace"
SANS: Final = "sans-serif"
CODE_FILL: Final = "#333333"
HEADING_RE: Final = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET_RE: Final = re.compile(r"^(\s*)[-*+]\s+(.*)$")
NUMBERED_RE: Final = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
BOLD_RE: Final = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
INLINE_RE: Final = re.compile(r"`([^`]*)`|\*([^*]+)\*|_([^_]+)_|!?\[([^\]]*)\]\([^)]*\)")
INDENT_PER_LEVEL: Final = 20.0
SPACES_PER_LEVEL: Final = 2

PHYSICAL_UNITS: Final = frozenset({Unit.MM, Unit.CM, Unit.IN, Unit.PT, Unit.PC})
"""Page size units that fix the printed size, so ``units_per_inch`` leaves them alone."""
