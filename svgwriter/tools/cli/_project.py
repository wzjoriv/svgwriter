"""
``new``, ``build``, ``presets`` and ``preview``: design projects (see :mod:`svgwriter.tools.project`).
"""

from __future__ import annotations

from pathlib import Path

import click

from ..project import PRESETS, Project
from ._constants import DEFAULT_PRESET, PRESET_COLUMN
from ._prompts import (
    ask_name,
    ask_notebook,
    ask_preset,
    ask_size,
    ask_theme,
    has_questionary,
    interactive,
    parse_size,
)

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
@click.argument("name", required=False)
@click.option("--preset", help="starter project (`svgwriter presets`); without it, a prompt asks")
@click.option("--notebook/--script", default=None, help="write main.ipynb instead of main.py")
@click.option("--theme", help="built-in theme that theme.toml extends (default: the preset's own)")
@click.option("--size", help="size name or WIDTH,HEIGHT written to svgwriter.toml (default: the preset's own)")
def new(name: str | None, preset: str | None, notebook: bool | None, theme: str | None, size: str | None) -> None:
    """Start a design project from a preset.

    NAME is the folder to create and the project name. In a terminal, missing choices are asked with
    arrow keys when questionary is installed (`pip install "pysvgwriter[cli]"`) and with a numbered menu
    otherwise; elsewhere they take the preset's defaults.
    """
    asking = interactive()
    fancy = asking and has_questionary()
    if name is None:
        if not asking:
            raise click.UsageError("missing argument NAME")
        name = ask_name() if fancy else click.prompt("Project name")
    if preset is None:
        preset = (ask_preset() if fancy else _choose_preset()) if asking else DEFAULT_PRESET
    choice: str | list[float | str] | None = parse_size(size) if size is not None else None
    if fancy:
        notebook = ask_notebook() if notebook is None else notebook
        theme = ask_theme() if theme is None else theme
        choice = ask_size() if size is None else choice
    project = Project.new(name, preset, notebook=bool(notebook), theme=theme, size=choice)
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
@click.option("--port", type=int, default=None, help="local port  [default: [preview] port, 8000]")
@click.option("--open/--no-open", "open_browser", default=None,
              help="open the page in a browser  [default: [preview] open, yes]")
@PROJECT_PATH
def preview(port: int | None, open_browser: bool | None, path: Path) -> None:
    """Serve a live page that redraws as controls move and files change."""
    project = Project.load(path)
    shown = project.config.preview.port if port is None else port
    click.echo(f"previewing {project.name} at http://127.0.0.1:{shown}/ (Ctrl+C stops)")
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
