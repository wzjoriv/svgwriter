"""
``svgwriter snippets``: render the docs' snippet pictures to look at them (the docs build makes its own).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ._snippets import OUTPUT, write_images

app = typer.Typer(name="snippets", help="Pictures of what the docs' code snippets draw.", no_args_is_help=True)


@app.command()
def build(out: Annotated[Path, typer.Option(help="Folder for the SVGs.")] = OUTPUT) -> None:
    """Render the pictures (the docs build does this itself; use this to look at them)."""
    found = write_images(out)
    typer.echo(f"{sum(map(len, found.values()))} block(s) with pictures on {len(found)} page(s) in {out}")
