"""Shared plumbing of the svgwriter Inkscape extensions.

Inkscape runs an extension as ``python <script> --param=value ... <drawing.svg>``
and reads the result from standard output. These helpers find svgwriter
(re-running the script with ``SVGWRITER_PYTHON`` when Inkscape's own Python
lacks it), parse the arguments, load the drawing and write it back.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from typing import IO, Any, NoReturn

__all__ = [
    "PYTHON_VARIABLE",
    "fail",
    "load",
    "multiline",
    "parser",
    "reported_warnings",
    "require_svgwriter",
    "selected",
    "write",
]

PYTHON_VARIABLE = "SVGWRITER_PYTHON"
RELAUNCHED = "SVGWRITER_RELAUNCHED"
NEWLINE_ESCAPE = "\\n"
INSTALL_HELP = (
    "svgwriter is not installed for the Python that Inkscape runs ({python}).\n"
    "Install it there (python -m pip install pysvgwriter), point Inkscape's python-interpreter "
    "preference at a Python that has it, or set the {variable} environment variable to such a "
    "Python. See plugins/inkscape/README.md."
)


def fail(message: str) -> NoReturn:
    """Show *message* in Inkscape's error dialog and stop."""
    sys.stderr.write(message.rstrip() + "\n")
    raise SystemExit(1)


@contextmanager
def reported_warnings() -> Iterator[None]:
    """Collect warnings (a missing font family, ...) and list each once on stderr, which Inkscape shows.

    Warnings never stop the extension: svgwriter falls back (a missing family
    resolves to a font installed on this system) and the drawing is still returned.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            yield
        finally:
            for message in dict.fromkeys(f"Warning: {warning.message}" for warning in caught):
                sys.stderr.write(message + "\n")


def require_svgwriter() -> None:
    """Import svgwriter, or re-run this script with the Python named by ``SVGWRITER_PYTHON``."""
    try:
        import svgwriter  # noqa: F401
    except ImportError:
        python = os.environ.get(PYTHON_VARIABLE)
        if python and not os.environ.get(RELAUNCHED):
            completed = subprocess.run([python, *sys.argv], env={**os.environ, RELAUNCHED: "1"}, check=False)
            raise SystemExit(completed.returncode) from None
        fail(INSTALL_HELP.format(python=sys.executable, variable=PYTHON_VARIABLE))


def parser(description: str) -> argparse.ArgumentParser:
    """An argument parser for Inkscape's calling convention.

    Unknown options are ignored, so Inkscape's own (``--tab``, notebook pages) do
    not break older scripts.
    """
    arguments = argparse.ArgumentParser(description=description)
    arguments.add_argument("input_file", nargs="?", help="the drawing; standard input when missing")
    arguments.add_argument("--id", action="append", default=[], dest="ids", help="ids of the selected objects")
    return arguments


def multiline(text: str) -> str:
    """Undo Inkscape's escaping of newlines in multiline text boxes."""
    return text.replace(NEWLINE_ESCAPE, "\n")


def load(path: str | None) -> Any:
    """The drawing as an svgwriter Document."""
    import svgwriter

    if path is None:
        return svgwriter.Document.from_string(sys.stdin.buffer.read())
    with open(path, "rb") as handle:
        return svgwriter.Document.from_string(handle.read())


def selected(doc: Any, ids: list[str]) -> list[Any]:
    """The elements Inkscape had selected, in selection order."""
    return [element for element in (doc.get_element_by_id(name) for name in ids) if element is not None]


def write(doc: Any, stream: IO[bytes] | None = None) -> None:
    """Send the drawing back to Inkscape as SVG on standard output."""
    target = stream if stream is not None else sys.stdout.buffer
    target.write(doc.to_string().encode("utf-8"))
    target.flush()
