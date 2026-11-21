"""
``animate``, ``render`` and ``outline``: commands needing ffmpeg or skia.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..document import Document
from ..video import FFmpegError, FFmpegNotFoundError, Scene, SceneError, load_scenes
from ..video.animation import DEFAULT_FPS, RENDERERS
from ._basic import emit, output_options
from ._constants import (
    DEFAULT_FONT,
    DEFAULT_TEXT_SIZE,
    EXIT_FAILURE,
    FRAME_FORMAT,
    TEXT_MARGIN,
)

__all__ = ["add_media_commands"]


def _fail(message: str) -> int:
    print(f"svgwriter: error: {message}", file=sys.stderr)
    return EXIT_FAILURE


def _targets(args: argparse.Namespace, extension: str | None) -> list[tuple[Scene, Path | None]]:
    scenes = load_scenes(args.scene, args.names)
    if args.output is not None and len(scenes) > 1:
        raise SceneError(f"-o names one file but {len(scenes)} scenes were selected; drop -o to write one file per scene")
    if args.output is not None:
        return [(scenes[0], Path(args.output))]
    return [(scene, Path(f"{scene.name}.{extension}") if extension else None) for scene in scenes]


def _cmd_animate(args: argparse.Namespace) -> int:
    try:
        if args.list:
            for scene in load_scenes(args.scene, args.names):
                print(scene.name)
            return 0
        for scene, target in _targets(args, args.format):
            print(scene.save(target, fps=args.fps, duration=args.duration, renderer=args.renderer, ffmpeg=args.ffmpeg))
    except (FFmpegNotFoundError, FFmpegError, ValueError) as exc:
        return _fail(str(exc))
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    try:
        targets = _targets(args, FRAME_FORMAT)
    except SceneError as exc:
        return _fail(str(exc))
    for scene, target in targets:
        written = target or Path(f"{scene.name}.{FRAME_FORMAT}")
        written.write_bytes(scene.render(args.time, scale=args.scale, background=args.background))
        print(written)
    return 0


def _cmd_outline(args: argparse.Namespace) -> int:
    from ..ops.text import text_to_path

    path = text_to_path(args.text, args.font, args.size, fill=args.fill)
    box = path.bbox
    document = Document(box.width + 2 * TEXT_MARGIN, box.height + 2 * TEXT_MARGIN)
    document += path.translate(TEXT_MARGIN - box.x, TEXT_MARGIN - box.y)
    emit(document.root, args)
    return 0


def add_media_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register ``animate``, ``render`` and ``outline``.

    Parameters
    ----------
    commands : argparse._SubParsersAction
        The sub-parser collection of the main parser.

    See Also
    --------
    svgwriter.cli._basic.add_basic_commands : The commands that need neither ffmpeg nor skia.
    """
    source_help = "scene file (.py), file.py:Name, package.module:Name, or an .svg file"
    names_help = "scene classes to pick (default: every Scene subclass the file defines)"
    animate = commands.add_parser(
        "animate",
        help="render scenes to mp4/gif/webm/png frames through ffmpeg",
        description="Render each svgwriter.Scene subclass in a file (or the ones named) frame by frame "
        "and encode it with ffmpeg to <Name>.<format>.",
    )
    animate.add_argument("scene", help=source_help)
    animate.add_argument("names", nargs="*", help=names_help)
    animate.add_argument("-o", "--out", "--output", dest="output", default=None, help="output file for a single scene; the extension picks the format")
    animate.add_argument("--format", default=None, help="extension of the <Name>.<format> files (default: mp4; png writes numbered frames)")
    animate.add_argument("--list", action="store_true", help="print the scene names and exit")
    animate.add_argument("--fps", type=float, default=None, help=f"frames per second (default: the scene's fps, {DEFAULT_FPS:g} unless set)")
    animate.add_argument("--duration", type=float, default=None, help="seconds (default: the scene's duration or the SMIL animation length)")
    animate.add_argument("--renderer", default=None, help=f"registered name ({', '.join(RENDERERS.names())}) or module:function (default: the scene's)")
    animate.add_argument("--ffmpeg", default=None, help="ffmpeg executable (default: found on PATH)")
    animate.set_defaults(func=_cmd_animate)

    render = commands.add_parser("render", help="rasterize scenes or an SVG file to PNG")
    render.add_argument("scene", help=source_help)
    render.add_argument("names", nargs="*", help=names_help)
    render.add_argument("-o", "--out", "--output", dest="output", default=None, help=f"output file for a single scene (default: <Name>.{FRAME_FORMAT})")
    render.add_argument("--time", type=float, default=0.0, help="seconds into the scene")
    render.add_argument("--scale", type=float, default=1.0, help="pixels per user unit")
    render.add_argument("--background", default=None, help="background color (default: transparent)")
    render.set_defaults(func=_cmd_render)

    outline = commands.add_parser("outline", help="write text as glyph outlines")
    outline.add_argument("text")
    outline.add_argument("--font", default=DEFAULT_FONT)
    outline.add_argument("--size", type=float, default=DEFAULT_TEXT_SIZE)
    outline.add_argument("--fill", default="black")
    output_options(outline)
    outline.set_defaults(func=_cmd_outline)
