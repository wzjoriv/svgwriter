"""The ``svgwriter`` command line (also ``python -m svgwriter``).

Commands
--------
shapes, elements    list registered composite shapes and element classes
sizes               list named canvas sizes
draw                write a registered shape
format, info        re-serialize or summarize an SVG file
animate             render the scenes of a file to mp4/gif/webm/png frames (ffmpeg)
render              rasterize scenes or an SVG file to PNG (skia-python)
outline             write text as glyph outlines (skia-python)
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Annotated

import typer

from .. import __version__
from ._basic import add_basic_commands
from ._constants import EXIT_ERROR
from ._media import add_media_commands

__all__ = ["app", "main"]

app = typer.Typer(name="svgwriter", help="Write, reformat, inspect and animate SVG 1.1 files.", add_completion=False,
                  no_args_is_help=True, pretty_exceptions_enable=False)
"""The ``svgwriter`` application; ``app.command()`` adds a command."""


def _version(shown: bool) -> None:
    if shown:
        print(f"svgwriter {__version__}")
        raise typer.Exit()


@app.callback()
def _options(version: Annotated[bool, typer.Option("--version", callback=_version, is_eager=True,
                                                   help="show the version and exit")] = False) -> None:
    """Write, reformat, inspect and animate SVG 1.1 files."""


add_basic_commands(app)
add_media_commands(app)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line.

    Parameters
    ----------
    argv : sequence of str, optional
        Arguments without the program name. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        The exit status: 0 on success, 1 when a command fails, 2 for a usage error or a file that
        cannot be read or written; errors are one line on stderr, without a traceback.

    Examples
    --------
    >>> from svgwriter.cli import main
    >>> main(["draw", "star", "--size", "50", "--compact"])  # doctest: +ELLIPSIS
    <?xml ...?>
    <svg ...</svg>0
    """
    try:
        app(args=list(argv) if argv is not None else None, prog_name="svgwriter")
    except SystemExit as done:
        return done.code if isinstance(done.code, int) else 0
    except (OSError, ValueError, TypeError) as error:
        print(f"svgwriter: error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return 0
