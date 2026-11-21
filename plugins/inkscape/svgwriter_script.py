"""Inkscape effect: run Python code on the open drawing with svgwriter.

The code sees ``doc`` (the drawing as a ``svgwriter.Document``), ``svg`` (the
svgwriter module), ``selection`` (the selected elements) and ``math``; the
drawing is written back to Inkscape when it finishes. Errors are reported with
the line number of the code that raised them.
"""

from __future__ import annotations

import math
import traceback
from pathlib import Path

from svgwriter_extension import fail, load, multiline, parser, reported_warnings, require_svgwriter, selected, write

__all__ = ["main", "run"]

SOURCE_NAME = "<svgwriter code>"


def _report(error: BaseException, source: str, name: str) -> str:
    lines = source.splitlines()
    frames = [frame for frame in traceback.extract_tb(error.__traceback__) if frame.filename == name]
    if isinstance(error, SyntaxError) and error.filename == name:
        number = error.lineno or 0
    elif frames:
        number = frames[-1].lineno or 0
    else:
        number = 0
    text = "".join(traceback.format_exception_only(type(error), error)).strip()
    if 0 < number <= len(lines):
        return f"Line {number}: {lines[number - 1].strip()}\n{text}"
    return text


def run(source: str, doc: object, selection: list[object], name: str = SOURCE_NAME) -> None:
    """Run *source* with ``doc``, ``svg``, ``selection`` and ``math`` defined.

    Raises
    ------
    SystemExit
        With the error and its line number when the code fails.
    """
    import svgwriter

    namespace = {"__name__": "__svgwriter__", "doc": doc, "svg": svgwriter, "selection": selection, "math": math}
    try:
        exec(compile(source, name, "exec"), namespace)
    except Exception as error:
        fail(_report(error, source, name))


def main(argv: list[str] | None = None) -> None:
    """Read the drawing, run the code from ``--code`` or ``--script`` and print the result."""
    require_svgwriter()
    arguments = parser("Run svgwriter code on an Inkscape drawing.")
    arguments.add_argument("--code", default="", help="Python code (Inkscape escapes newlines as \\n)")
    arguments.add_argument("--script", default="", help="a .py file to run instead of --code")
    options, _ = arguments.parse_known_args(argv)
    if options.script:
        script = Path(options.script)
        if not script.is_file():
            fail(f"script not found: {script}")
        source, name = script.read_text(encoding="utf-8"), str(script)
    else:
        source, name = multiline(options.code), SOURCE_NAME
    doc = load(options.input_file)
    run(source, doc, selected(doc, options.ids), name)
    write(doc)


if __name__ == "__main__":
    with reported_warnings():
        main()
