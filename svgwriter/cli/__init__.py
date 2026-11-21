"""The ``python -m svgwriter`` command line.

Commands
--------
shapes, elements    list registered composite shapes and element classes
draw                write a registered shape
format, info        re-serialize or summarize an SVG file
animate             render the scenes of a file to mp4/gif/webm/png frames (ffmpeg)
render              rasterize scenes or an SVG file to PNG (skia-python)
outline             write text as glyph outlines (skia-python)
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import Final

from .. import __version__
from ._basic import add_basic_commands
from ._media import add_media_commands

EXIT_ERROR: Final = 2

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    """Build the ``svgwriter`` argument parser with every sub-command attached.

    Returns
    -------
    argparse.ArgumentParser
        The parser used by :func:`main`.

    See Also
    --------
    main : Parse arguments and run a command.

    Examples
    --------
    >>> from svgwriter.cli import build_parser
    >>> args = build_parser().parse_args(["draw", "star", "--size", "50"])
    >>> args.command, args.shape, args.size
    ('draw', 'star', 50.0)
    """
    parser = argparse.ArgumentParser(prog="svgwriter", description="Write, reformat, inspect and animate SVG 1.1 files.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    add_basic_commands(commands)
    add_media_commands(commands)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line.

    Parameters
    ----------
    argv : sequence of str, optional
        Arguments without the program name. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        The process exit status; 0 on success.

    Raises
    ------
    SystemExit
        With status 2 when a file cannot be read or written or its contents
        are invalid; the message is printed as one line, without a traceback.

    See Also
    --------
    build_parser : The parser that interprets `argv`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, TypeError) as error:
        parser.exit(EXIT_ERROR, f"{parser.prog}: error: {error}\n")
