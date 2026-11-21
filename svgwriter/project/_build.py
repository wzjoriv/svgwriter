"""
Writing a project's outputs: pages through the exporters, scenes as GIF frames or baked SMIL, video through ffmpeg.

Still formats (PDF, PNG, ...) show a page once its animations have ended; ``seconds = 0`` in the format's
options shows the start instead.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from .._document.sizes import PageSize
from .._internal._codecs._gif import encode_gif_animation
from .._internal._codecs._rgba import to_uint8
from ..document import Document
from ..export import exporters, save
from ..theme import Theme
from ..video import Scene, animation_duration, frame_times
from ..widgets import controls_of
from ._config import ProjectConfig
from ._constants import ANIMATED_FORMATS, BAKED_FORMATS, DEFAULT_GIF_FPS, KEEPS_ANIMATION, VIDEO_FORMATS
from ._entry import Item

__all__ = ["control_arguments", "write_outputs"]


def _extension(format: str) -> str:
    exporter = exporters().get(format)
    return exporter.extensions[0] if exporter is not None and exporter.extensions else f".{format}"


def control_arguments(function: Any, values: Mapping[str, Any]) -> dict[str, Any]:
    """Keyword arguments for the controls *function* declares: *values* where given, else the starting values."""
    controls = controls_of(function, infer=False)
    return {name: control.argument(control.check(values[name]) if name in values else control.initial)
            for name, control in controls.items()}


def _page(config: ProjectConfig, function: Any, values: Mapping[str, Any]) -> Document:
    if isinstance(config.size, (str, PageSize)):
        doc = Document(size=config.size)
    elif config.size is not None:
        doc = Document(*config.size)
    else:
        doc = Document()
    result = function(doc, **control_arguments(function, values))
    return result if isinstance(result, Document) else doc


def _numbered(stem: str, count: int, extension: str) -> list[str]:
    if count == 1:
        return [f"{stem}{extension}"]
    width = len(str(count))
    return [f"{stem}-{index:0{width}d}{extension}" for index in range(1, count + 1)]


def _gif(scene: Scene, options: Mapping[str, Any]) -> bytes | None:
    """The scene's frames, ``update`` included, as an animated GIF; None when nothing moves."""
    fps = float(options.get("fps", DEFAULT_GIF_FPS))
    length = options.get("duration") or scene.duration or animation_duration(scene.document)
    if not length:
        return None
    raster = {key: options[key] for key in ("scale", "background") if key in options}
    frames = []
    for seconds in frame_times(fps, float(length)):
        scene._advance(scene.document, seconds)
        frames.append(to_uint8(scene.document.at(seconds).rasterize(**raster)))
    return encode_gif_animation(frames, fps, loop=int(options.get("loop", 0)))


def _write_scene(scene: Scene, target: Path, format: str, options: Mapping[str, Any]) -> Path:
    if format in VIDEO_FORMATS:
        return scene.save(target, fps=options.get("fps"), duration=options.get("duration"),
                          ffmpeg=options.get("ffmpeg"))
    if format in ANIMATED_FORMATS:
        data = _gif(scene, options)
        if data is not None:
            target.write_bytes(data)
            return target
    duration = options.get("duration")
    if format in BAKED_FORMATS and (duration or scene.duration or animation_duration(scene.document)):
        baked = scene.bake(options.get("fps"), duration=duration)
        return save(baked, target, format, **{k: v for k, v in options.items() if k not in ("fps", "duration")})
    scene._advance(scene.document, 0.0)
    return save(scene.document, target, format, **options)


def _settled(page: Document) -> Document:
    """*page* as it looks once its animations have ended, for still formats."""
    end = animation_duration(page)
    return page.at(end) if end else page


def _write_pages(pages: Sequence[Document], targets: list[Path], format: str, options: Mapping[str, Any]) -> list[Path]:
    if format in VIDEO_FORMATS:
        return [_write_scene(Scene(page), target, format, options) for page, target in zip(pages, targets, strict=True)]
    if format not in KEEPS_ANIMATION and "seconds" not in options:
        pages = [_settled(page) for page in pages]
    exporter = exporters().get(format)
    if len(pages) > 1 and exporter is not None and exporter.multipage:
        return [save(list(pages), targets[0], format, **options)]
    return [save(page, target, format, **options) for page, target in zip(pages, targets, strict=True)]


def write_outputs(config: ProjectConfig, items: Sequence[Item], theme: Theme | None,
                  formats: Sequence[str], values: Mapping[str, Any] | None = None) -> list[Path]:
    """Draw every page and scene with the project's size and theme, then write each format; return the files.

    Page functions with declared controls receive *values* for them, or their starting values.
    """
    folder = config.root / config.output
    folder.mkdir(parents=True, exist_ok=True)
    with theme if theme is not None else nullcontext():
        scenes = [item if isinstance(item, Scene) else item() for item in items
                  if isinstance(item, Scene) or isinstance(item, type) and issubclass(item, Scene)]
        pages = [_page(config, item, values or {}) for item in items if not isinstance(item, (Scene, type))]
    written: list[Path] = []
    for format in formats:
        options = config.options.get(format, {})
        extension = _extension(format)
        if pages:
            exporter = exporters().get(format)
            one_file = exporter is not None and exporter.multipage and format not in VIDEO_FORMATS
            names = _numbered(config.name, 1 if one_file else len(pages), extension)
            written += _write_pages(pages, [folder / name for name in names], format, options)
        for scene in scenes:
            stem = config.name if len(scenes) == 1 and not pages else f"{config.name}-{scene.name}"
            written.append(_write_scene(scene, folder / f"{stem}{extension}", format, options))
    return written
