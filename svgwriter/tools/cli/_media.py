"""
``animate``, ``render`` and ``outline``: commands needing ffmpeg or skia.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import click

from ...document import Document
from ...errors import FFmpegError, FFmpegNotFoundError, SceneError
from ...motion.video import Scene, load_scenes
from ...motion.video.animation import DEFAULT_FPS, renderers
from ._basic import emit, output_options
from ._constants import DEFAULT_FONT, DEFAULT_TEXT_SIZE, EXIT_FAILURE, FRAME_FORMAT, TEXT_MARGIN

__all__ = ["add_media_commands", "fail"]

SCENE_HELP = "scene file (.py), file.py:Name, package.module:Name, or an .svg file"


def fail(message: str) -> click.exceptions.Exit:
    """Print *message* as a one-line error and return the exit to raise.

    Parameters
    ----------
    message : str
        What went wrong.

    Returns
    -------
    click.exceptions.Exit
        An exit with status 1.

    Examples
    --------
    >>> from svgwriter.tools.cli._media import fail
    >>> fail("no scenes").exit_code
    1
    """
    click.secho(f"svgwriter: error: {message}", fg="red", err=True)
    return click.exceptions.Exit(EXIT_FAILURE)


def _targets(source: str, names: Sequence[str], output: str | None,
             extension: str | None) -> list[tuple[Scene, Path | None]]:
    scenes = load_scenes(source, names)
    if output is not None and len(scenes) > 1:
        raise SceneError(f"-o names one file but {len(scenes)} scenes were selected; drop -o to write one file per scene")
    if output is not None:
        return [(scenes[0], Path(output))]
    return [(scene, Path(f"{scene.name}.{extension}") if extension else None) for scene in scenes]


@click.command()
@click.argument("source", metavar="SCENE")
@click.argument("names", nargs=-1)
@click.option("-o", "--out", "--output", "output",
              help="output file for a single scene; the extension picks the format")
@click.option("--format", "extension",
              help="extension of the <Name>.<format> files (default: mp4; png writes numbered frames)")
@click.option("--list", "list_", is_flag=True, help="print the scene names and exit")
@click.option("--fps", type=float, help=f"frames per second (default: the scene's fps, {DEFAULT_FPS:g} unless set)")
@click.option("--duration", type=float, help="seconds (default: the scene's duration or the SMIL animation length)")
@click.option("--renderer",
              help=f"registered name ({', '.join(renderers.list())}) or module:function (default: the scene's)")
@click.option("--ffmpeg", help="ffmpeg executable (default: found on PATH)")
def animate(source: str, names: tuple[str, ...], output: str | None, extension: str | None, list_: bool,
            fps: float | None, duration: float | None, renderer: str | None, ffmpeg: str | None) -> None:
    """Render scenes to mp4/gif/webm/png frames through ffmpeg.

    SCENE is a scene file (.py), file.py:Name, package.module:Name, or an .svg file. Each svgwriter.Scene
    subclass in it (or the NAMES given) is rendered frame by frame and encoded with ffmpeg to <Name>.<format>.
    """
    try:
        if list_:
            for scene in load_scenes(source, names):
                click.echo(scene.name)
            return
        for scene, target in _targets(source, names, output, extension):
            click.echo(scene.save(target, fps=fps, duration=duration, renderer=renderer, ffmpeg=ffmpeg))
    except (FFmpegNotFoundError, FFmpegError, ValueError) as exc:
        raise fail(str(exc)) from None


@click.command()
@click.argument("source", metavar="SCENE")
@click.argument("names", nargs=-1)
@click.option("-o", "--out", "--output", "output",
              help=f"output file for a single scene (default: <Name>.{FRAME_FORMAT})")
@click.option("--at", "seconds", type=float, default=0.0, show_default=True, metavar="SECONDS",
              help="moment to render, in seconds from the start")
@click.option("--scale", type=float, default=1.0, show_default=True, help="pixels per user unit")
@click.option("--background", help="background color (default: transparent)")
def render(source: str, names: tuple[str, ...], output: str | None, seconds: float, scale: float,
           background: str | None) -> None:
    """Rasterize scenes or an SVG file to PNG.

    SCENE is a scene file (.py), file.py:Name, package.module:Name, or an .svg file; NAMES picks scene classes.
    """
    try:
        targets = _targets(source, names, output, FRAME_FORMAT)
    except SceneError as exc:
        raise fail(str(exc)) from None
    for scene, target in targets:
        written = target or Path(f"{scene.name}.{FRAME_FORMAT}")
        written.write_bytes(scene.render(seconds, scale=scale, background=background))
        click.echo(written)


@click.command()
@click.argument("text")
@click.option("--font", default=DEFAULT_FONT, show_default=True, help="font family")
@click.option("--size", type=float, default=DEFAULT_TEXT_SIZE, show_default=True, help="font size")
@click.option("--fill", default="black", show_default=True, help="fill color")
@output_options
def outline(text: str, font: str, size: float, fill: str, output: str | None, compact: bool, precision: int) -> None:
    """Write text as glyph outlines."""
    from ...ops.text import text_to_path

    path = text_to_path(text, font, size, fill=fill)
    box = path.bbox
    document = Document(box.width + 2 * TEXT_MARGIN, box.height + 2 * TEXT_MARGIN)
    document += path.translate(TEXT_MARGIN - box.x, TEXT_MARGIN - box.y)
    emit(document.root, output, compact, precision)


def add_media_commands(app: click.Group) -> None:
    """Register ``animate``, ``render`` and ``outline``.

    Parameters
    ----------
    app : click.Group
        The command line application.

    See Also
    --------
    svgwriter.tools.cli._basic.add_basic_commands : The commands that need neither ffmpeg nor skia.
    """
    for command in (animate, render, outline):
        app.add_command(command)
