"""
External command-line tools: finding them, running them and reading the SVG they write.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from ._constants import INSTALL_HINT, TIMEOUT_SECONDS

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["DiagramToolError", "find_tool", "run_tool", "svg_document"]


class DiagramToolError(RuntimeError):
    """The diagram tool is missing or rejected the input.

    See Also
    --------
    svgwriter.formats.export._diagram.read_dot, svgwriter.formats.export._diagram.read_mermaid : The importers that run the tools.

    Examples
    --------
    >>> from svgwriter._internal._tools import DiagramToolError
    >>> issubclass(DiagramToolError, RuntimeError)
    True
    """


def find_tool(name: str) -> str:
    """The executable for *name*, from ``SVGWRITER_<NAME>`` or ``PATH``."""
    found = os.environ.get(f"SVGWRITER_{name.upper()}") or shutil.which(name)
    if not found:
        raise DiagramToolError(f"`{name}` not found; {INSTALL_HINT[name]}")
    return found


def run_tool(command: list[str], data: bytes | None = None) -> bytes:
    """Run a tool, returning its standard output or raising with its error text."""
    try:
        done = subprocess.run(command, input=data, capture_output=True, timeout=TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DiagramToolError(f"{Path(command[0]).name} failed: {error}") from error
    if done.returncode != 0:
        message = done.stderr.decode("utf-8", "replace").strip() or f"exit status {done.returncode}"
        raise DiagramToolError(f"{Path(command[0]).name}: {message}")
    return done.stdout


def svg_document(svg_text: bytes) -> Document:
    from ..document import Document

    return Document.from_string(svg_text.decode("utf-8"))
