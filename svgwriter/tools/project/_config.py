"""
The project manifest: ``svgwriter.toml``, or ``[tool.svgwriter]`` in ``pyproject.toml``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomlkit

from ..._document.sizes import PageSize, page_size
from ...errors import ProjectError
from ...formats import writers as format_writers
from ...model.attributes.length import Length
from ...model.color import parse_color
from ._constants import (
    ANIMATED_FORMATS,
    BACKGROUNDS,
    DEFAULT_ENTRY,
    DEFAULT_FORMATS,
    DEFAULT_OUTPUT,
    DEFAULT_PORT,
    FITS,
    FONT_FOLDER,
    LAYOUTS,
    MANIFEST,
    OUTPUT_KEYS,
    PREVIEW_DEBOUNCE_MS,
    PREVIEW_KEYS,
    PROJECT_KEYS,
    PYPROJECT,
    PYPROJECT_TABLE,
    TOP_KEYS,
    VIDEO_FORMATS,
)

__all__ = ["PreviewConfig", "ProjectConfig", "check_formats", "check_preview", "check_size",
           "find_manifest", "read_config"]

SizeSpec = str | PageSize | tuple[Length, Length] | None



@dataclass(frozen=True)
class PreviewConfig:
    """How ``svgwriter preview`` shows a project, read from the manifest's ``[preview]`` table.

    Parameters
    ----------
    pages : tuple of str or None
        The pages and scenes to show, by output name, in this order. None shows all of them.
    background : str
        Behind the drawing: ``"checker"``, ``"light"``, ``"dark"`` or a colour.
    layout : str
        Where the controls sit: ``"auto"`` (right of the drawing on wide windows, below it otherwise),
        ``"right"`` or ``"bottom"``.
    fit : str
        ``"contain"`` scales the drawing to its area; ``"actual"`` shows it at its own size.
    port : int
        The local port.
    open : bool
        Open the page in a browser on start.
    debounce_ms : int
        Milliseconds the page waits after a control moves before asking for a new drawing.
    build_on_save : bool
        Write the outputs after a file is saved and the project has been quiet for a moment.
    formats_on_build : tuple of str or None
        The formats that saving and the page's Build outputs button write. None writes ``[outputs] formats``.

    Examples
    --------
    >>> from svgwriter.tools.project import PreviewConfig
    >>> PreviewConfig().layout, PreviewConfig().port
    ('auto', 8000)
    """

    pages: tuple[str, ...] | None = None
    background: str = BACKGROUNDS[0]
    layout: str = LAYOUTS[0]
    fit: str = FITS[0]
    port: int = DEFAULT_PORT
    open: bool = True
    debounce_ms: int = PREVIEW_DEBOUNCE_MS
    build_on_save: bool = True
    formats_on_build: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ProjectConfig:
    """The settings of a project, read from its manifest.

    Parameters
    ----------
    root : pathlib.Path
        The project folder (where the manifest is).
    source : pathlib.Path
        The file the settings came from.
    name : str
        The project name; output files are named after it.
    entry : str
        ``"module:object"`` or ``"notebook.ipynb:object"``.
    size : str, PageSize, (Length, Length) or None
        A named size, a :class:`~svgwriter.PageSize` or a width and height for the documents handed to the entry.
    theme : str or None
        A theme file (relative to `root`) or a registered theme name.
    fonts : str
        Folder whose font files are registered before building.
    formats : tuple of str
        Output formats, in order.
    options : Mapping
        Exporter options per format.
    output : str
        Output folder, relative to `root`.
    preview : PreviewConfig
        How ``svgwriter preview`` shows the project.

    Examples
    --------
    >>> from pathlib import Path
    >>> from svgwriter.tools.project import ProjectConfig
    >>> ProjectConfig(Path("."), Path("svgwriter.toml"), "demo").formats
    ('svg', 'png')
    """

    root: Path
    source: Path
    name: str
    entry: str = DEFAULT_ENTRY
    size: SizeSpec = None
    theme: str | None = None
    fonts: str = FONT_FOLDER
    formats: tuple[str, ...] = DEFAULT_FORMATS
    options: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    output: str = DEFAULT_OUTPUT
    preview: PreviewConfig = field(default_factory=PreviewConfig)


def _table(document: Mapping[str, Any], path: tuple[str, ...]) -> Mapping[str, Any] | None:
    for key in path:
        if not isinstance(document, Mapping) or key not in document:
            return None
        document = document[key]
    return document if isinstance(document, Mapping) else None


def _read(path: Path) -> dict[str, Any]:
    try:
        return tomlkit.parse(path.read_text(encoding="utf-8")).unwrap()
    except tomlkit.exceptions.TOMLKitError as error:
        raise ProjectError(f"{path}: {error}") from None


def find_manifest(start: Path) -> tuple[Path, Mapping[str, Any]]:
    """The nearest ``svgwriter.toml``, or ``pyproject.toml`` with a ``[tool.svgwriter]`` table, at or above *start*."""
    folder = start.resolve()
    for candidate in (folder, *folder.parents):
        manifest = candidate / MANIFEST
        if manifest.is_file():
            return manifest, _read(manifest)
        pyproject = candidate / PYPROJECT
        if pyproject.is_file():
            table = _table(_read(pyproject), PYPROJECT_TABLE)
            if table is not None:
                return pyproject, table
    raise ProjectError(f"no {MANIFEST} (or [tool.svgwriter] in {PYPROJECT}) in {folder} or above; "
                       "create a project with `svgwriter new NAME`")


def _unknown(source: Path, where: str, keys: Mapping[str, Any], allowed: frozenset[str]) -> None:
    for key in keys:
        if key not in allowed:
            raise ProjectError(f"{source}: unknown key {where}{key!r}; expected one of {', '.join(sorted(allowed))}")


def check_size(source: Path, value: object) -> SizeSpec:
    """*value* as a size spec; a bad one raises :class:`ProjectError` naming *source*."""
    if value is None:
        return None
    try:
        if isinstance(value, (str, PageSize)):
            page_size(value)
            return value
        if isinstance(value, list) and len(value) == 2:
            width, height = (Length.parse(side) if isinstance(side, str) else Length(float(side)) for side in value)
            return width, height
    except (ValueError, TypeError) as error:
        raise ProjectError(f"{source}: project.size: {error}") from None
    raise ProjectError(f"{source}: project.size is a size name such as \"a4\" or [width, height], not {value!r}")


def check_formats(where: str, formats: Sequence[object]) -> tuple[str, ...]:
    """*formats* in lower case; an unknown one raises :class:`ProjectError` naming *where*."""
    known = {*format_writers(), *ANIMATED_FORMATS, *VIDEO_FORMATS}
    names = tuple(str(name).lower() for name in formats)
    for name in names:
        if name not in known:
            raise ProjectError(f"{where}: unknown format {name!r}; expected one of {', '.join(sorted(known))}")
    return names


def _choice(source: Path, key: str, value: object, choices: Sequence[str]) -> str:
    if value not in choices:
        raise ProjectError(f"{source}: preview.{key} is one of {', '.join(map(repr, choices))}, not {value!r}")
    return str(value)


def _flag(source: Path, key: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ProjectError(f"{source}: preview.{key} is true or false, not {value!r}")
    return value


def _count(source: Path, key: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProjectError(f"{source}: preview.{key} is a whole number of at least 0, not {value!r}")
    return value


def _names(source: Path, key: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(name, str) for name in value):
        raise ProjectError(f"{source}: preview.{key} is a list of names, not {value!r}")
    return tuple(value)


def _background(source: Path, value: object) -> str:
    if value in BACKGROUNDS:
        return str(value)
    try:
        parse_color(str(value))
    except (TypeError, ValueError):
        raise ProjectError(f"{source}: preview.background is one of {', '.join(map(repr, BACKGROUNDS))} "
                           f"or a colour, not {value!r}") from None
    return str(value)


def check_preview(source: Path, table: Mapping[str, Any]) -> PreviewConfig:
    """The ``[preview]`` table as a :class:`PreviewConfig`; an unknown key or bad value raises :class:`ProjectError`."""
    if not isinstance(table, Mapping):
        raise ProjectError(f"{source}: preview is a table, not {table!r}")
    _unknown(source, "preview.", table, PREVIEW_KEYS)
    default = PreviewConfig()
    formats = table.get("formats_on_build")
    return PreviewConfig(
        pages=_names(source, "pages", table["pages"]) if "pages" in table else None,
        background=_background(source, table.get("background", default.background)),
        layout=_choice(source, "layout", table.get("layout", default.layout), LAYOUTS),
        fit=_choice(source, "fit", table.get("fit", default.fit), FITS),
        port=_count(source, "port", table.get("port", default.port)),
        open=_flag(source, "open", table.get("open", default.open)),
        debounce_ms=_count(source, "debounce_ms", table.get("debounce_ms", default.debounce_ms)),
        build_on_save=_flag(source, "build_on_save", table.get("build_on_save", default.build_on_save)),
        formats_on_build=None if formats is None else check_formats(
            f"{source}: preview.formats_on_build", _names(source, "formats_on_build", formats)))


def read_config(start: Path) -> ProjectConfig:
    """Find and check the manifest for the project at or above *start*."""
    source, data = find_manifest(start)
    _unknown(source, "", data, TOP_KEYS)
    project = data.get("project", {})
    outputs = data.get("outputs", {})
    _unknown(source, "project.", project, PROJECT_KEYS)
    _unknown(source, "outputs.", outputs, OUTPUT_KEYS | {*format_writers(), *ANIMATED_FORMATS, *VIDEO_FORMATS})
    formats = check_formats(f"{source}: outputs.formats", outputs.get("formats", DEFAULT_FORMATS))
    options: dict[str, dict[str, Any]] = {}
    for key, value in outputs.items():
        if key in OUTPUT_KEYS:
            continue
        if not isinstance(value, Mapping):
            raise ProjectError(f"{source}: outputs.{key} is a table of exporter options, not {value!r}")
        options[key] = dict(value)
    root = source.parent
    return ProjectConfig(root=root, source=source, name=str(project.get("name", root.name)),
                         entry=str(project.get("entry", DEFAULT_ENTRY)), size=check_size(source, project.get("size")),
                         theme=project.get("theme"), fonts=str(project.get("fonts", FONT_FOLDER)), formats=formats,
                         options=options, output=str(outputs.get("directory", DEFAULT_OUTPUT)),
                         preview=check_preview(source, data.get("preview", {})))
