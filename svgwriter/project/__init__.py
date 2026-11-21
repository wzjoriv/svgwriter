"""Design projects: a folder with ``svgwriter.toml``, its drawing code, theme, assets and outputs.

``svgwriter new NAME --preset poster`` starts one from a preset, ``svgwriter build`` writes its outputs and
``svgwriter preview`` shows them in a browser that reloads on every save. In Python, :class:`Project` does
the same: ``svg.Project.load().build()``. Presets are a registry (:func:`register_preset`).

Example
-------
>>> import svgwriter as svg, tempfile
>>> with tempfile.TemporaryDirectory() as folder:
...     project = svg.Project.new(f"{folder}/poster", preset="poster")
...     print(project.config.size, [path.suffix for path in project.build(["svg", "png"])])
a4 ['.svg', '.png']
"""

from __future__ import annotations

from ._config import ProjectConfig, ProjectError
from ._gallery import Preview
from .presets import PRESETS, Preset, register_preset, unregister_preset
from .project import Project

__all__ = [
    "PRESETS",
    "Preset",
    "Preview",
    "Project",
    "ProjectConfig",
    "ProjectError",
    "register_preset",
    "unregister_preset",
]
