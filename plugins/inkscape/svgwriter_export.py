"""Inkscape effect: save the open drawing through svgwriter to another format.

Any format svgwriter exports works (``pptx`` with animations, ``tikz``,
``gcode``, ``pdf``, ...). The drawing itself is returned to Inkscape unchanged.
"""

from __future__ import annotations

import ast
from pathlib import Path

from svgwriter_extension import fail, load, multiline, parser, reported_warnings, require_svgwriter, write

__all__ = ["main", "options_from_text"]

OPTION_SEPARATORS = (",", "\n")
FROM_EXTENSION = "auto"


def options_from_text(text: str) -> dict[str, object]:
    """Exporter options from ``name=value`` pairs separated by commas or lines.

    Values are Python literals (``300``, ``True``, ``"mm"``); anything else is
    kept as text.
    """
    options: dict[str, object] = {}
    for separator in OPTION_SEPARATORS[1:]:
        text = text.replace(separator, OPTION_SEPARATORS[0])
    for item in filter(None, (part.strip() for part in text.split(OPTION_SEPARATORS[0]))):
        name, equals, value = item.partition("=")
        if not equals:
            fail(f"exporter option {item!r} needs the form name=value")
        try:
            options[name.strip()] = ast.literal_eval(value.strip())
        except (ValueError, SyntaxError):
            options[name.strip()] = value.strip()
    return options


def main(argv: list[str] | None = None) -> None:
    """Export the drawing to ``--output`` in ``--format`` and echo it back."""
    require_svgwriter()
    arguments = parser("Save an Inkscape drawing through svgwriter.")
    arguments.add_argument("--output", default="", help="file to write")
    arguments.add_argument("--format", default=FROM_EXTENSION, help="exporter name, or auto for the file extension")
    arguments.add_argument("--options", default="", help="exporter options as name=value pairs")
    options, _ = arguments.parse_known_args(argv)
    if not options.output:
        fail("choose a file to save to")
    doc = load(options.input_file)
    target = Path(options.output).expanduser()
    chosen = None if options.format == FROM_EXTENSION else options.format
    try:
        doc.save(target, format=chosen, **options_from_text(multiline(options.options)))
    except (ValueError, TypeError, OSError, ImportError) as error:
        fail(f"could not save {target}: {error}")
    write(doc)


if __name__ == "__main__":
    with reported_warnings():
        main()
