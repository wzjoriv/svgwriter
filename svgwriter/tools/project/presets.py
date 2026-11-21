"""
Project presets: starter folders that ``svgwriter new`` copies, kept in a registry.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import tomlkit

from ..._internal._constants import ENTRY_POINT_PREFIX
from ..._internal._registry import Registry
from ._config import ProjectError, check_size
from ._constants import (
    BUILTIN_PRESETS,
    DOT_PREFIX,
    MANIFEST,
    NOTEBOOK_SUFFIX,
    PLACEHOLDERS,
    TEMPLATE_SUFFIX,
    TEMPLATES,
    THEME_FILE,
)
from ._notebook import notebook_of

SizeChoice = str | Sequence[float | str]

__all__ = ["PRESETS", "Preset", "ProjectPresets", "create"]


@dataclass(frozen=True)
class Preset:
    """A starter project: a folder of files, optionally laid over another preset's.

    In the folder, a ``-tpl`` suffix is dropped from file names (``main.py-tpl`` becomes ``main.py``, so the
    templates are not importable modules) and a ``dot-`` prefix becomes a dot (``dot-gitignore``). Text files
    have ``{{ project_name }}`` and ``{{ preset }}`` replaced.

    Parameters
    ----------
    name : str
        The name given to ``svgwriter new --preset``.
    description : str
        One line for ``svgwriter presets``.
    directory : pathlib.Path
        The folder copied into the new project.
    extends : str or None, optional
        A preset whose files are copied first. Defaults to None.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.project.PRESETS.get("poster").extends
    'blank'
    """

    name: str
    description: str
    directory: Path
    extends: str | None = None


class ProjectPresets(Registry[Preset]):
    """Project presets by name: what ``svgwriter new NAME --preset <name>`` and :meth:`Project.new` start from.

    Register a :class:`Preset` with :meth:`register` (its folder must exist and ``extends`` name a registered
    preset); ``svgwriter presets`` lists them. Packages add presets through the ``svgwriter.project_preset``
    entry-point group.

    Examples
    --------
    >>> import svgwriter as svg, tempfile
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     preset = svg.project.PRESETS.register(svg.project.Preset("badge", "A round badge", folder, "blank"))
    ...     print("badge" in svg.project.PRESETS.list())
    ...     _ = svg.project.PRESETS.unregister("badge")
    True
    """

    def prepare(self, name: str, item: Preset) -> Preset:
        path = Path(item.directory)
        if not path.is_dir():
            raise ValueError(f"preset {name!r}: no folder {path}")
        if item.extends is not None:
            self.get(item.extends)
        return Preset(name, item.description, path, item.extends)


PRESETS: Final = ProjectPresets("preset", group=ENTRY_POINT_PREFIX + "project_preset")
"""Every project preset by name; ``svgwriter presets`` lists them."""


def _find(name: str) -> Preset:
    """The preset registered as *name*; an unknown name raises :class:`ProjectError` listing the presets."""
    found = PRESETS.find(name)
    if found is None:
        raise ProjectError(f"{PRESETS.unknown(name)}; presets: {', '.join(PRESETS.list())}")
    return found


def _layers(preset: Preset) -> list[Preset]:
    chain = [preset]
    while chain[-1].extends is not None:
        chain.append(_find(chain[-1].extends))
    return chain[::-1]


def _target_name(relative: Path) -> Path:
    parts = [part.removesuffix(TEMPLATE_SUFFIX) for part in relative.parts]
    parts = [f".{part.removeprefix(DOT_PREFIX)}" if part.startswith(DOT_PREFIX) else part for part in parts]
    return Path(*parts)


def _render(data: bytes, values: dict[str, str]) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    for key, value in values.items():
        text = text.replace(PLACEHOLDERS[key], value)
    return text.encode("utf-8")


def _unstyled(table: Any, key: str, value: object) -> None:
    table[key] = value
    trivia = table.item(key).trivia
    trivia.comment = trivia.comment_ws = ""


def _chosen(files: dict[Path, bytes], size: SizeChoice | None, theme: str | None) -> None:
    from ...model.theme import THEMES

    manifest, theme_file = Path(MANIFEST), Path(THEME_FILE)
    if size is not None:
        check_size(manifest, size if isinstance(size, str) else list(size))
        document = tomlkit.parse(files[manifest].decode("utf-8"))
        _unstyled(document["project"], "size", size if isinstance(size, str) else list(size))
        files[manifest] = tomlkit.dumps(document).encode("utf-8")
    if theme is None:
        return
    if theme not in THEMES:
        raise ProjectError(f"unknown theme {theme!r}; themes: {', '.join(THEMES.list())}")
    target, key = (theme_file, None) if theme_file in files else (manifest, "theme")
    document = tomlkit.parse(files[target].decode("utf-8"))
    _unstyled(document if key is None else document["project"], key or "extends", theme)
    files[target] = tomlkit.dumps(document).encode("utf-8")


def create(path: str | os.PathLike[str], preset: str = "blank", *, notebook: bool = False,
           name: str | None = None, theme: str | None = None, size: SizeChoice | None = None) -> Path:
    """Write a new project folder from *preset*; return the folder (see :meth:`svgwriter.Project.new`)."""
    folder = Path(path)
    chosen = _find(preset)
    if folder.exists() and any(folder.iterdir()):
        raise ProjectError(f"{folder} already exists and is not empty; choose a new folder name")
    values = {"project_name": name or folder.resolve().name, "preset": chosen.name}
    files: dict[Path, bytes] = {}
    for layer in _layers(chosen):
        for source in sorted(layer.directory.rglob("*")):
            if source.is_file() and "__pycache__" not in source.parts:
                files[_target_name(source.relative_to(layer.directory))] = _render(source.read_bytes(), values)
    _chosen(files, size, theme)
    if notebook:
        script = files.pop(Path("main.py"), None)
        if script is None:
            raise ProjectError(f"preset {chosen.name!r} has no main.py to turn into a notebook")
        files[Path(f"main{NOTEBOOK_SUFFIX}")] = json.dumps(notebook_of(script.decode("utf-8")), indent=1).encode("utf-8")
        manifest = files[Path(MANIFEST)].decode("utf-8")
        files[Path(MANIFEST)] = manifest.replace('entry = "main:', f'entry = "main{NOTEBOOK_SUFFIX}:').encode("utf-8")
    for relative, data in files.items():
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return folder


for _name, (_description, _extends) in BUILTIN_PRESETS.items():
    PRESETS.add_builtin(_name, Preset(_name, _description, TEMPLATES / _name, _extends))
