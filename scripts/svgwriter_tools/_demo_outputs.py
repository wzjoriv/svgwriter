"""
``svgwriter demo-outputs``: build each demo's light outputs (SVG, PDF, PNG, PPTX) into its ``output/`` folder, where
they are committed so readers can open them without running anything.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

ROOT = Path(__file__).resolve().parents[2]
DEMOS = ROOT / "demos"
LIGHT = ("svg", "pdf", "png", "pptx")
"""Formats small enough to commit; video and GIF stay local."""

app = typer.Typer(name="demo-outputs", help="The demos' committed outputs (SVG, PDF, PNG, PPTX).",
                  no_args_is_help=True)


def demo_names() -> list[str]:
    """Every demo folder with a project file."""
    return sorted(path.parent.name for path in DEMOS.glob("*/svgwriter.toml"))


def light_formats(name: str) -> list[str]:
    """The demo's output formats that are committed."""
    import svgwriter as svg

    return [format for format in svg.Project.load(DEMOS / name).config.formats if format in LIGHT]


@app.command()
def build(names: Annotated[list[str] | None, typer.Argument(help="Only these demos.")] = None) -> None:
    """Build the light outputs of every demo (or the named ones) into demos/<name>/output/."""
    import svgwriter as svg

    for name in names or demo_names():
        formats = light_formats(name)
        if not formats:
            continue
        written = svg.Project.load(DEMOS / name).build(formats)
        typer.echo(f"{name}: {', '.join(path.name for path in written)}")


@app.command()
def check() -> None:
    """Exit 1 when a demo has no committed output for one of its light formats."""
    missing = []
    for name in demo_names():
        folder = DEMOS / name / "output"
        missing += [f"{name}: no .{format}" for format in light_formats(name)
                    if not any(folder.glob(f"*.{format}"))]
    for line in missing:
        typer.echo(line, err=True)
    if missing:
        typer.echo("run `python scripts/dev.py svgwriter demo-outputs build`", err=True)
        raise typer.Exit(1)
    typer.echo("demo outputs present")
