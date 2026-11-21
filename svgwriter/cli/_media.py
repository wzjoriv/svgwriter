"""
``animate``, ``render`` and ``outline``: commands needing ffmpeg or skia.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from ..document import Document
from ..video import FFmpegError, FFmpegNotFoundError, Scene, SceneError, load_scenes
from ..video.animation import DEFAULT_FPS, RENDERERS
from ._basic import PRECISION, Compact, Output, Precision, emit
from ._constants import DEFAULT_FONT, DEFAULT_TEXT_SIZE, EXIT_FAILURE, FRAME_FORMAT, TEXT_MARGIN

__all__ = ["add_media_commands", "fail"]

Source = Annotated[str, typer.Argument(metavar="SCENE",
                                       help="scene file (.py), file.py:Name, package.module:Name, or an .svg file")]
Names = Annotated[list[str] | None, typer.Argument(
    help="scene classes to pick (default: every Scene subclass the file defines)", show_default=False)]
SceneOutput = Annotated[str | None, typer.Option("-o", "--out", "--output",
                                                 help="output file for a single scene; the extension picks the format")]


def fail(message: str) -> typer.Exit:
    """Print *message* as a one-line error and return the exit to raise.

    Parameters
    ----------
    message : str
        What went wrong.

    Returns
    -------
    typer.Exit
        An exit with status 1.

    Examples
    --------
    >>> from svgwriter.cli._media import fail
    >>> fail("no scenes").exit_code
    1
    """
    print(f"svgwriter: error: {message}", file=sys.stderr)
    return typer.Exit(EXIT_FAILURE)


def _targets(source: str, names: list[str] | None, output: str | None,
             extension: str | None) -> list[tuple[Scene, Path | None]]:
    scenes = load_scenes(source, names or ())
    if output is not None and len(scenes) > 1:
        raise SceneError(f"-o names one file but {len(scenes)} scenes were selected; drop -o to write one file per scene")
    if output is not None:
        return [(scenes[0], Path(output))]
    return [(scene, Path(f"{scene.name}.{extension}") if extension else None) for scene in scenes]


def animate(source: Source, names: Names = None, output: SceneOutput = None,
            format: Annotated[str | None, typer.Option(
                "--format", help="extension of the <Name>.<format> files (default: mp4; png writes numbered frames)")] = None,
            list_: Annotated[bool, typer.Option("--list", help="print the scene names and exit")] = False,
            fps: Annotated[float | None, typer.Option(
                help=f"frames per second (default: the scene's fps, {DEFAULT_FPS:g} unless set)")] = None,
            duration: Annotated[float | None, typer.Option(
                help="seconds (default: the scene's duration or the SMIL animation length)")] = None,
            renderer: Annotated[str | None, typer.Option(
                help=f"registered name ({', '.join(RENDERERS.names())}) or module:function (default: the scene's)")] = None,
            ffmpeg: Annotated[str | None, typer.Option(help="ffmpeg executable (default: found on PATH)")] = None) -> None:
    """Render scenes to mp4/gif/webm/png frames through ffmpeg.

    Each svgwriter.Scene subclass in a file (or the ones named) is rendered frame by frame and encoded with ffmpeg to <Name>.<format>.
    """
    try:
        if list_:
            for scene in load_scenes(source, names or ()):
                print(scene.name)
            return
        for scene, target in _targets(source, names, output, format):
            print(scene.save(target, fps=fps, duration=duration, renderer=renderer, ffmpeg=ffmpeg))
    except (FFmpegNotFoundError, FFmpegError, ValueError) as exc:
        raise fail(str(exc)) from None


def render(source: Source, names: Names = None,
           output: Annotated[str | None, typer.Option(
               "-o", "--out", "--output", help=f"output file for a single scene (default: <Name>.{FRAME_FORMAT})")] = None,
           time: Annotated[float, typer.Option(help="seconds into the scene")] = 0.0,
           scale: Annotated[float, typer.Option(help="pixels per user unit")] = 1.0,
           background: Annotated[str | None, typer.Option(help="background color (default: transparent)")] = None) -> None:
    """Rasterize scenes or an SVG file to PNG."""
    try:
        targets = _targets(source, names, output, FRAME_FORMAT)
    except SceneError as exc:
        raise fail(str(exc)) from None
    for scene, target in targets:
        written = target or Path(f"{scene.name}.{FRAME_FORMAT}")
        written.write_bytes(scene.render(time, scale=scale, background=background))
        print(written)


def outline(text: str, font: Annotated[str, typer.Option(help="font family")] = DEFAULT_FONT,
            size: Annotated[float, typer.Option(help="font size")] = DEFAULT_TEXT_SIZE,
            fill: Annotated[str, typer.Option(help="fill color")] = "black",
            output: Output = None, compact: Compact = False, precision: Precision = PRECISION) -> None:
    """Write text as glyph outlines."""
    from ..ops.text import text_to_path

    path = text_to_path(text, font, size, fill=fill)
    box = path.bbox
    document = Document(box.width + 2 * TEXT_MARGIN, box.height + 2 * TEXT_MARGIN)
    document += path.translate(TEXT_MARGIN - box.x, TEXT_MARGIN - box.y)
    emit(document.root, output, compact, precision)


def add_media_commands(app: typer.Typer) -> None:
    """Register ``animate``, ``render`` and ``outline``.

    Parameters
    ----------
    app : typer.Typer
        The command line application.

    See Also
    --------
    svgwriter.cli._basic.add_basic_commands : The commands that need neither ffmpeg nor skia.
    """
    for command in (animate, render, outline):
        app.command()(command)
