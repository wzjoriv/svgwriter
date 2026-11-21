"""
Project presets: starter folders that ``svgwriter new`` copies, kept in a registry.
"""

from __future__ import annotations

import difflib
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import tomlkit

from .._internal._registry import Registry
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

__all__ = ["PRESETS", "Preset", "create", "find_preset", "register_preset", "unregister_preset"]


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


PRESETS: Final[Registry[Preset]] = Registry("preset")
"""Every project preset by name; ``svgwriter presets`` lists them."""


def register_preset(name: str, directory: str | os.PathLike[str], description: str, *,
                    extends: str | None = None) -> Preset:
    """Add a project preset that ``svgwriter new NAME --preset <name>`` and :meth:`Project.new` can start from.

    Parameters
    ----------
    name : str
        The preset name.
    directory : str or os.PathLike
        The folder to copy (see :class:`Preset` for the file name rules).
    description : str
        One line for ``svgwriter presets``.
    extends : str, optional
        A registered preset whose files are copied first, so this folder only holds what differs.
        Defaults to None.

    Returns
    -------
    Preset
        The registered preset.

    Raises
    ------
    ValueError
        If the name is taken, the folder does not exist, or `extends` is not registered.

    See Also
    --------
    unregister_preset : Remove it again.

    Examples
    --------
    >>> import svgwriter as svg, tempfile
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     preset = svg.project.register_preset("badge", folder, "A round badge", extends="blank")
    ...     print(preset.name in svg.project.PRESETS)
    ...     svg.project.unregister_preset("badge")
    True
    """
    path = Path(directory)
    if not path.is_dir():
        raise ValueError(f"preset {name!r}: no folder {path}")
    if extends is not None:
        find_preset(extends)
    return PRESETS.add(name, Preset(name, description, path, extends))


def unregister_preset(name: str) -> None:
    """Remove a preset added with :func:`register_preset`.

    Parameters
    ----------
    name : str
        The registered name.

    Raises
    ------
    KeyError
        If no preset has that name.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.project.unregister_preset("nope")
    Traceback (most recent call last):
    ...
    KeyError: "unknown preset 'nope'"
    """
    PRESETS.remove(name)


def find_preset(name: str) -> Preset:
    """The preset registered as *name*; an unknown name raises :class:`ProjectError` listing the presets."""
    if name not in PRESETS:
        close = difflib.get_close_matches(name, PRESETS.names(), n=1)
        hint = f"did you mean {close[0]!r}? " if close else ""
        raise ProjectError(f"unknown preset {name!r}; {hint}presets: {', '.join(PRESETS.names())}")
    return PRESETS.get(name)


def _layers(preset: Preset) -> list[Preset]:
    chain = [preset]
    while chain[-1].extends is not None:
        chain.append(find_preset(chain[-1].extends))
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
    from ..model.theme import THEMES

    manifest, theme_file = Path(MANIFEST), Path(THEME_FILE)
    if size is not None:
        check_size(manifest, size if isinstance(size, str) else list(size))
        document = tomlkit.parse(files[manifest].decode("utf-8"))
        _unstyled(document["project"], "size", size if isinstance(size, str) else list(size))
        files[manifest] = tomlkit.dumps(document).encode("utf-8")
    if theme is None:
        return
    if theme not in THEMES:
        raise ProjectError(f"unknown theme {theme!r}; themes: {', '.join(THEMES.names())}")
    target, key = (theme_file, None) if theme_file in files else (manifest, "theme")
    document = tomlkit.parse(files[target].decode("utf-8"))
    _unstyled(document if key is None else document["project"], key or "extends", theme)
    files[target] = tomlkit.dumps(document).encode("utf-8")


def create(path: str | os.PathLike[str], preset: str = "blank", *, notebook: bool = False,
           name: str | None = None, theme: str | None = None, size: SizeChoice | None = None) -> Path:
    """Write a new project folder from *preset*; return the folder (see :meth:`svgwriter.Project.new`)."""
    folder = Path(path)
    chosen = find_preset(preset)
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
    PRESETS.add(_name, Preset(_name, _description, TEMPLATES / _name, _extends))
