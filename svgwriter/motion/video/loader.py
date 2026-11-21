"""
Finding the scenes in a file, a module or an ``.svg`` drawing.
"""

from __future__ import annotations

import importlib
import runpy
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ...errors import SceneError
from ._constants import SCENE_RUN_NAME, SCENE_SCRIPT, SCENE_SVG
from .scene import Scene

__all__ = ["load_scenes"]



def _split(source: str) -> tuple[str, str | None]:
    head, sep, attribute = source.rpartition(":")
    if sep and attribute.isidentifier() and len(head) > 1:
        return head, attribute
    return source, None


def _namespace(head: str) -> dict[str, Any]:
    path = Path(head)
    if path.suffix.lower() == SCENE_SCRIPT or path.is_file():
        return runpy.run_path(str(path), run_name=SCENE_RUN_NAME)
    return vars(importlib.import_module(head))


def _as_scene(name: str, value: object) -> Scene | None:
    from ...document import Document

    if isinstance(value, Scene):
        return value
    if isinstance(value, type) and issubclass(value, Scene) and value is not Scene:
        return value()
    if isinstance(value, Document):
        return Scene(value, name=name)
    return None


def _defined(namespace: dict[str, Any]) -> list[Scene]:
    module = namespace.get("__name__")
    return [
        value()
        for name, value in namespace.items()
        if isinstance(value, type) and issubclass(value, Scene) and value is not Scene
        and value.__module__ == module and not name.startswith("_")
    ]


def load_scenes(source: str | Path, names: Sequence[str] = ()) -> list[Scene]:
    """Collect scenes from a script, a module or an ``.svg`` file.

    `source` is a path to a Python file, an importable module name, either
    one followed by ``:Name``, or an ``.svg`` file. Without names, every
    :class:`Scene` subclass the file or module defines is returned, in
    definition order; classes whose names start with ``_`` are skipped, so
    a shared base class can be private. A name may also refer to a scene
    instance or a :class:`~svgwriter.Document`.

    Parameters
    ----------
    source : str or pathlib.Path
        ``"scenes.py"``, ``"scenes.py:Intro"``, ``"pkg.scenes:Intro"`` or
        ``"drawing.svg"``.
    names : sequence of str, optional
        Scenes to pick, in this order. Defaults to all of them.

    Returns
    -------
    list of Scene
        New instances, ready to save.

    Raises
    ------
    SceneError
        If nothing matches, or a name is not a scene.

    See Also
    --------
    Scene : What the file defines.

    Examples
    --------
    >>> from svgwriter.motion.video import load_scenes
    >>> [scene.name for scene in load_scenes("svgwriter.motion.video.scene:Scene")]
    Traceback (most recent call last):
    ...
    svgwriter.errors.SceneError: 'Scene' in svgwriter.motion.video.scene is not a scene
    """
    text = str(source)
    if Path(text).suffix.lower() == SCENE_SVG:
        from ...document import Document

        return [Scene(Document.open(text), name=Path(text).stem)]
    head, attribute = _split(text)
    wanted = [*([attribute] if attribute else []), *names]
    namespace = _namespace(head)
    if not wanted:
        scenes = _defined(namespace)
        if not scenes:
            raise SceneError(f"{head} defines no svgwriter.Scene subclass")
        return scenes
    scenes = []
    for name in wanted:
        scene = _as_scene(name, namespace.get(name))
        if scene is None:
            raise SceneError(f"{name!r} in {head} is not a scene")
        scenes.append(scene)
    return scenes
