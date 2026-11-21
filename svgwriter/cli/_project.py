"""
``new``, ``build``, ``presets`` and ``preview``: design projects (see :mod:`svgwriter.project`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..project import PRESETS, Project
from ._constants import PRESET_COLUMN, PREVIEW_PORT

__all__ = ["add_project_commands"]

Folder = Annotated[Path, typer.Option("--path", help="the project folder, or one inside it")]


def _choose_preset() -> str:
    """Ask for a preset with a numbered menu."""
    names = PRESETS.names()
    for index, name in enumerate(names, 1):
        print(f"{index:>2}. {name:<{PRESET_COLUMN}} {PRESETS.get(name).description}")
    choice = typer.prompt("Preset", default="1")
    if choice in names:
        return choice
    if not choice.isdigit() or not 1 <= int(choice) <= len(names):
        raise typer.BadParameter(f"{choice!r} is not a number from 1 to {len(names)} or a preset name",
                                 param_hint="preset")
    return names[int(choice) - 1]


def new(name: Annotated[str, typer.Argument(help="folder to create; also the project name")],
        preset: Annotated[str | None, typer.Option(
            help="starter project (`svgwriter presets`); without it, a menu asks")] = None,
        notebook: Annotated[bool, typer.Option(help="write main.ipynb instead of main.py")] = False) -> None:
    """Start a design project from a preset."""
    project = Project.new(name, preset or _choose_preset(), notebook=notebook)
    print(f"created {project.root}")
    print(f"next: cd {name} && svgwriter preview")


def build(format: Annotated[list[str] | None, typer.Option(
              "--format", "-f", help="only this format (repeat for more; default: [outputs] formats)")] = None,
          path: Folder = Path(".")) -> None:
    """Write the project's outputs into its output folder."""
    for written in Project.load(path).build(format or None):
        print(written)


def presets() -> None:
    """List project presets."""
    for name in PRESETS.names():
        print(f"{name:<{PRESET_COLUMN}} {PRESETS.get(name).description}")


def preview(port: Annotated[int, typer.Option(help="local port")] = PREVIEW_PORT,
            open_browser: Annotated[bool, typer.Option("--open/--no-open", help="open the page in a browser")] = True,
            path: Folder = Path(".")) -> None:
    """Serve the outputs on a local page that rebuilds and reloads on every save."""
    project = Project.load(path)
    print(f"previewing {project.name} at http://127.0.0.1:{port}/ (Ctrl+C stops)")
    project.serve(port, open_browser=open_browser)


def add_project_commands(app: typer.Typer) -> None:
    """Register ``new``, ``build``, ``presets`` and ``preview``.

    Parameters
    ----------
    app : typer.Typer
        The command line application.

    See Also
    --------
    svgwriter.Project : What the commands drive.
    """
    for command in (new, build, presets, preview):
        app.command()(command)
