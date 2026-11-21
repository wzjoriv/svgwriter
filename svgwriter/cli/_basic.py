"""
``shapes``, ``sizes``, ``elements``, ``draw``, ``format`` and ``info``.
"""

from __future__ import annotations

import sys
from collections import Counter
from typing import Annotated

import typer

from .._document.sizes import SIZES
from ..builder import SHAPES
from ..document import Document
from ..elements.core import Category, Element
from ..io.parser import Strictness, parse_file
from ..io.writer import SerializeOptions
from ._constants import CANVAS_MARGIN, DEFAULT_CANVAS, DRAW_LAYOUTS, SIZE_COLUMN, STROKE_WIDTH

__all__ = ["Compact", "Output", "Precision", "add_basic_commands", "emit"]

Output = Annotated[str | None, typer.Option("-o", "--output", help="write here instead of stdout")]
Compact = Annotated[bool, typer.Option("--compact", help="single-line output, shortest path data")]
Precision = Annotated[int, typer.Option("--precision", help="significant digits of numbers")]
PRECISION = SerializeOptions().precision


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
    >>> from svgwriter.cli._basic import emit
    >>> emit(svg.Svg(), None, compact=True, precision=3)  # doctest: +ELLIPSIS
    <?xml ...?>
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1"/>
    """
    options = SerializeOptions(pretty=not compact, precision=precision, compact_paths=compact)
    if output:
        root.save(output, options=options)
    else:
        sys.stdout.write(root.to_string(options=options))


def shapes() -> None:
    """List registered composite shapes."""
    for name in SHAPES.names():
        print(name)


def sizes() -> None:
    """List named canvas sizes (Document(size=...))."""
    for name in SIZES.names():
        width, height = SIZES.get(name)
        print(f"{name:<{SIZE_COLUMN}} {width} x {height}")


def elements() -> None:
    """List supported elements by category."""
    for category in Category:
        tags = sorted(Element.registered(category))
        if tags:
            print(f"{category.name.lower()}: {' '.join(tags)}")


def draw(shape: Annotated[str, typer.Argument(help="a name from `svgwriter shapes`")],
         size: Annotated[float, typer.Option(help="canvas size")] = DEFAULT_CANVAS,
         fill: Annotated[str, typer.Option(help="fill color")] = "steelblue",
         stroke: Annotated[str | None, typer.Option(help="stroke color")] = None,
         output: Output = None, compact: Compact = False, precision: Precision = PRECISION) -> None:
    """Render a registered shape."""
    if shape not in SHAPES:
        raise typer.BadParameter(f"{shape!r} is not one of {', '.join(SHAPES.names())}", param_hint="SHAPE")
    doc = Document(size, size)
    center, radius = size / 2, size * CANVAS_MARGIN
    factory = SHAPES.get(shape)
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


def format_file(source: Annotated[str, typer.Argument(metavar="INPUT", help="the SVG file")],
                output: Output = None, compact: Compact = False, precision: Precision = PRECISION) -> None:
    """Parse a file and write it back out."""
    emit(parse_file(source, strictness=Strictness.WARN), output, compact, precision)


def info(source: Annotated[str, typer.Argument(metavar="INPUT", help="the SVG file")]) -> None:
    """Count elements in a file."""
    counts = Counter(element.tag for element in parse_file(source).iter())
    for tag, count in counts.most_common():
        print(f"{count:6d}  {tag}")


def add_basic_commands(app: typer.Typer) -> None:
    """Register ``shapes``, ``sizes``, ``elements``, ``draw``, ``format`` and ``info``.

    Parameters
    ----------
    app : typer.Typer
        The command line application.

    See Also
    --------
    svgwriter.cli._media.add_media_commands : The commands that need ffmpeg or skia.
    """
    for command in (shapes, sizes, elements, draw):
        app.command()(command)
    app.command("format")(format_file)
    app.command()(info)
