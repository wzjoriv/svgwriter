"""The ``svgwriter`` command line (also ``python -m svgwriter``).

Commands
--------
new                 start a design project from a preset
build               write a project's outputs
presets             list project presets
preview             serve a live page that redraws as controls move and files change
shapes, elements    list registered composite shapes and element classes
sizes               list named canvas sizes
draw                write a registered shape
format, info        re-serialize or summarize an SVG file
animate             render the scenes of a file to mp4/gif/webm/png frames (ffmpeg)
render              rasterize scenes or an SVG file to PNG (skia-python)
outline             write text as glyph outlines (skia-python)
doctor              what works here, what is missing and how to install it

Packages add commands through the ``svgwriter.command`` entry-point group (see :data:`commands`).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

import click

from ... import __version__
from ..._internal._registry import Registry
from ._basic import add_basic_commands
from ._constants import EXIT_ERROR, EXIT_FAILURE
from ._doctor import add_doctor_command
from ._media import add_media_commands
from ._project import add_project_commands

__all__ = ["commands", "app", "main"]

commands: Final[Registry[click.Command]] = Registry("command")
"""Commands beside the built-in ones: ``commands.register(command)``, or the ``svgwriter.command`` entry points.

Examples
--------
>>> import click
>>> from svgwriter.tools.cli import commands, main
>>> @commands.register
... @click.command(help="Say hello.")
... def hello() -> None:
...     click.echo("hello")
>>> main(["hello"])
hello
0
>>> _ = commands.unregister("hello")
"""


class _Commands(click.Group):
    """The built-in commands, then the ones in :data:`commands`."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted({*super().list_commands(ctx), *commands.list()})

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return super().get_command(ctx, cmd_name) or commands.find(cmd_name)


@click.group(name="svgwriter", cls=_Commands, invoke_without_command=True,
             help="Start design projects and build them; write, reformat, inspect and animate SVG 1.1 files.")
@click.version_option(__version__, "--version", prog_name="svgwriter", message="%(prog)s %(version)s",
                      help="show the version and exit")
@click.pass_context
def app(context: click.Context) -> None:
    """The ``svgwriter`` application: a :class:`click.Group`; ``app.add_command(command)`` adds a command."""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())


add_project_commands(app)
add_basic_commands(app)
add_media_commands(app)
add_doctor_command(app)


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
    >>> from svgwriter.tools.cli import main
    >>> main(["draw", "star", "--size", "50", "--compact"])  # doctest: +ELLIPSIS
    <?xml ...?>
    <svg ...</svg>0
    """
    try:
        status = app.main(args=list(argv) if argv is not None else None, prog_name="svgwriter", standalone_mode=False)
    except click.ClickException as error:
        error.show()
        return error.exit_code
    except click.Abort:
        click.secho("Aborted!", fg="red", err=True)
        return EXIT_FAILURE
    except (OSError, ValueError, TypeError) as error:
        click.secho(f"svgwriter: error: {error}", fg="red", err=True)
        return EXIT_ERROR
    return status if isinstance(status, int) else 0
