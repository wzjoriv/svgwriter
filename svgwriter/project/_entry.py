"""
Loading a project's code: imports scoped to its folder, the entry object, its theme and its fonts.
"""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .._internal._presets import KINDS
from ..theme import Theme
from ..video import Scene
from ._config import ProjectConfig, ProjectError
from ._constants import DEFAULT_NOTEBOOK_OBJECT, FONT_SUFFIXES, NOTEBOOK_SUFFIX

__all__ = ["Item", "entry_parts", "items_of", "load_object", "load_theme", "project_scope", "register_fonts",
           "working_directory"]

Item = type[Scene] | Scene | Callable[..., Any]

_FONTS: set[tuple[Path, float]] = set()


def _local_names(root: Path) -> set[str]:
    """Top-level module names that the project folder provides."""
    names = {path.stem for path in root.glob("*.py")}
    names.update(path.name for path in root.iterdir() if path.is_dir() and (path / "__init__.py").is_file())
    return names


def _inside(module: object, root: Path) -> bool:
    file = getattr(module, "__file__", None)
    return bool(file) and Path(file).resolve().is_relative_to(root)


@contextmanager
def working_directory(root: Path) -> Generator[None, None, None]:
    """Run the block with *root* as the current folder, so the project's relative paths resolve."""
    previous = Path.cwd()
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(previous)


@contextmanager
def project_scope(root: Path) -> Generator[None, None, None]:
    """Import from *root* without bytecode caches; afterwards forget its modules and the presets and sizes they registered.

    Cached bytecode is keyed on modification time and size, so an edit within the same second that keeps
    the size would otherwise load the old code.
    """
    root = root.resolve()
    shadowed = {name: sys.modules.pop(name) for name in _local_names(root) if name in sys.modules}
    presets = {kind: registry.state() for kind, registry in KINDS.items()}
    writes_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    try:
        yield
    finally:
        sys.dont_write_bytecode = writes_bytecode
        sys.path.remove(str(root))
        for name, module in list(sys.modules.items()):
            if _inside(module, root):
                del sys.modules[name]
        sys.modules.update(shadowed)
        for kind, state in presets.items():
            KINDS[kind].restore(state)


def entry_parts(config: ProjectConfig) -> tuple[str, str]:
    """``(module or notebook, object name)`` of the entry; the object defaults to ``build``."""
    target, _, attribute = config.entry.rpartition(":") if ":" in config.entry else (config.entry, "", "")
    return target, attribute or DEFAULT_NOTEBOOK_OBJECT


def load_object(config: ProjectConfig) -> object:
    """Import the entry module (inside :func:`project_scope`) and return the entry object."""
    target, attribute = entry_parts(config)
    where = f"{config.source}: project.entry {config.entry!r}"
    if target.endswith(NOTEBOOK_SUFFIX):
        raise ProjectError(f"{where}: notebooks run through svgwriter.project, not import")
    try:
        module = importlib.import_module(target)
    except ModuleNotFoundError as error:
        if error.name != target.partition(".")[0] and error.name != target:
            raise
        raise ProjectError(f"{where}: no module {target!r} in {config.root}") from None
    try:
        return getattr(module, attribute)
    except AttributeError:
        raise ProjectError(f"{where}: {Path(module.__file__ or target).name} has no {attribute!r}") from None


def items_of(config: ProjectConfig, value: object) -> list[Item]:
    """The entry object as a list of page functions and scenes."""
    items = list(value) if isinstance(value, (list, tuple)) else [value]
    for item in items:
        scene = isinstance(item, Scene) or (isinstance(item, type) and issubclass(item, Scene))
        if not scene and not callable(item):
            raise ProjectError(f"{config.source}: project.entry {config.entry!r} gives {type(item).__name__}; "
                               "expected a function taking a Document, a Scene class, or a list of them")
    return items


def load_theme(config: ProjectConfig) -> Theme | None:
    """The project's theme: a TOML file in the project, or a registered theme name."""
    if config.theme is None:
        return None
    path = config.root / config.theme
    if path.suffix == ".toml" or path.is_file():
        if not path.is_file():
            raise ProjectError(f"{config.source}: project.theme: no file {config.theme!r} in {config.root}")
        try:
            return Theme.load(path)
        except ValueError as error:
            raise ProjectError(f"{path}: {error}") from None
    try:
        return Theme.get(config.theme)
    except KeyError as error:
        raise ProjectError(f"{config.source}: project.theme: {error.args[0]}") from None


def register_fonts(config: ProjectConfig) -> list[str]:
    """Register every font file in the project's font folder once (again when it changes); return the families."""
    from ..ops import register_font

    folder = config.root / config.fonts
    families = []
    for path in sorted(folder.glob("*")) if folder.is_dir() else []:
        key = (path.resolve(), path.stat().st_mtime)
        if path.suffix.lower() in FONT_SUFFIXES and key not in _FONTS:
            families.append(register_font(path))
            _FONTS.add(key)
    return families
