"""
``shapes``, ``sizes``, ``elements``, ``draw``, ``format`` and ``info``.
"""

from __future__ import annotations

import sys
from collections import Counter
from collections.abc import Callable
from typing import Any

import click

from ...catalog import preset
from ...document import Document
from ...formats.io.parser import Strictness, parse_file
from ...formats.io.writer import SerializeOptions
from ...model.elements.core import Category, Element
from ._constants import CANVAS_MARGIN, DEFAULT_CANVAS, DRAW_LAYOUTS, SIZE_COLUMN, STROKE_WIDTH

__all__ = ["PRECISION", "add_basic_commands", "emit", "output_options"]

PRECISION = SerializeOptions().precision


def output_options(command: Callable[..., Any]) -> Callable[..., Any]:
    """Add ``-o/--output``, ``--compact`` and ``--precision`` to *command*, which receives them as keywords."""
    for option in (
        click.option("--precision", type=int, default=PRECISION, show_default=True, help="significant digits of numbers"),
        click.option("--compact", is_flag=True, help="single-line output, shortest path data"),
        click.option("-o", "--output", help="write here instead of stdout"),
    ):
        command = option(command)
    return command


def emit(root: Element, output: str | None, compact: bool, precision: int) -> None:
    """Write *root* to *output*, or to stdout when it is None.

    Parameters
    ----------
    root : Element
        Root of the tree to write.
    output : str or None
        The file to write, or None for stdout.
    compact : bool
        Single-line output with the shortest path data.
    precision : int
        Significant digits of numbers.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.tools.cli._basic import emit
    >>> emit(svg.Svg(), None, compact=True, precision=3)  # doctest: +ELLIPSIS
    <?xml ...?>
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1"/>
    """
    options = SerializeOptions(pretty=not compact, precision=precision, compact_paths=compact)
    if output:
        root.save(output, options=options)
    else:
        sys.stdout.write(root.to_string(options=options))


@click.command()
def shapes() -> None:
    """List registered composite shapes."""
    for name in preset.list("shape"):
        click.echo(name)


@click.command()
def sizes() -> None:
    """List named canvas sizes (Document(size=...))."""
    for name in preset.list("size"):
        click.echo(f"{name:<{SIZE_COLUMN}} {preset.get('size', name)}")


@click.command()
def elements() -> None:
    """List supported elements by category."""
    for category in Category:
        tags = sorted(Element.registered(category))
        if tags:
            click.echo(f"{category.name.lower()}: {' '.join(tags)}")


@click.command()
@click.argument("shape", metavar="SHAPE")
@click.option("--size", type=float, default=DEFAULT_CANVAS, show_default=True, help="canvas size")
@click.option("--fill", default="steelblue", show_default=True, help="fill color")
@click.option("--stroke", help="stroke color")
@output_options
def draw(shape: str, size: float, fill: str, stroke: str | None, output: str | None, compact: bool, precision: int) -> None:
    """Render a registered shape (a name from `svgwriter shapes`)."""
    try:
        factory = preset.get("shape", shape)
    except KeyError as error:
        raise click.BadParameter(error.args[0], param_hint="SHAPE") from None
    doc = Document(size, size)
    center, radius = size / 2, size * CANVAS_MARGIN
    layout = DRAW_LAYOUTS.get(shape)
    if layout is None:
        drawn = factory(center, center, radius, fill=fill, stroke=stroke)
    else:
        lead, options = layout(center, radius)
        line = options.pop("line", False)
        stroked = {"stroke": fill, "stroke_width": STROKE_WIDTH} if line else {"fill": fill, "stroke": stroke}
        drawn = factory(*lead, **options, **stroked)
    doc += drawn
    emit(doc.root, output, compact, precision)


@click.command("format")
@click.argument("source", metavar="INPUT")
@output_options
def format_file(source: str, output: str | None, compact: bool, precision: int) -> None:
    """Parse a file and write it back out."""
    emit(parse_file(source, strictness=Strictness.WARN), output, compact, precision)


@click.command()
@click.argument("source", metavar="INPUT")
def info(source: str) -> None:
    """Count elements in a file."""
    counts = Counter(element.tag for element in parse_file(source).iter())
    for tag, count in counts.most_common():
        click.echo(f"{count:6d}  {tag}")


def add_basic_commands(app: click.Group) -> None:
    """Register ``shapes``, ``sizes``, ``elements``, ``draw``, ``format`` and ``info``.

    Parameters
    ----------
    app : click.Group
        The command line application.

    See Also
    --------
    svgwriter.tools.cli._media.add_media_commands : The commands that need ffmpeg or skia.
    """
    for command in (shapes, sizes, elements, draw, format_file, info):
        app.add_command(command)
