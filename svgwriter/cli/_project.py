"""
``new``, ``build``, ``presets`` and ``preview``: design projects (see :mod:`svgwriter.project`).
"""

from __future__ import annotations

from pathlib import Path

import click

from ..project import PRESETS, Project
from ._constants import PRESET_COLUMN, PREVIEW_PORT

__all__ = ["add_project_commands"]

PROJECT_PATH = click.option("--path", type=click.Path(path_type=Path), default=Path("."), show_default=True,
                            help="the project folder, or one inside it")


def _choose_preset() -> str:
    """Ask for a preset with a numbered menu."""
    names = PRESETS.names()
    for index, name in enumerate(names, 1):
        click.echo(f"{index:>2}. {name:<{PRESET_COLUMN}} {PRESETS.get(name).description}")
    choice = click.prompt("Preset", default=1, type=click.IntRange(1, len(names)))
    return names[choice - 1]


@click.command()
@click.argument("name")
@click.option("--preset", help="starter project (`svgwriter presets`); without it, a menu asks")
@click.option("--notebook", is_flag=True, help="write main.ipynb instead of main.py")
def new(name: str, preset: str | None, notebook: bool) -> None:
    """Start a design project from a preset.

    NAME is the folder to create and the project name.
    """
    project = Project.new(name, preset or _choose_preset(), notebook=notebook)
    click.echo(f"created {project.root}")
    click.echo(f"next: cd {name} && svgwriter preview")


@click.command()
@click.option("--format", "-f", "formats", multiple=True,
              help="only this format (repeat for more; default: [outputs] formats)")
@PROJECT_PATH
def build(formats: tuple[str, ...], path: Path) -> None:
    """Write the project's outputs into its output folder."""
    for written in Project.load(path).build(list(formats) or None):
        click.echo(written)


@click.command()
def presets() -> None:
    """List project presets."""
    for name in PRESETS.names():
        click.echo(f"{name:<{PRESET_COLUMN}} {PRESETS.get(name).description}")


@click.command()
@click.option("--port", type=int, default=PREVIEW_PORT, show_default=True, help="local port")
@click.option("--open/--no-open", "open_browser", default=True, help="open the page in a browser")
@PROJECT_PATH
def preview(port: int, open_browser: bool, path: Path) -> None:
    """Serve the outputs on a local page that rebuilds and reloads on every save."""
    project = Project.load(path)
    click.echo(f"previewing {project.name} at http://127.0.0.1:{port}/ (Ctrl+C stops)")
    project.serve(port, open_browser=open_browser)


def add_project_commands(app: click.Group) -> None:
    """Register ``new``, ``build``, ``presets`` and ``preview``.

    Parameters
    ----------
    app : click.Group
        The command line application.

    See Also
    --------
    svgwriter.Project : What the commands drive.
    """
    for command in (new, build, presets, preview):
        app.add_command(command)
