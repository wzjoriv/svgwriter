"""Design projects: a folder with ``svgwriter.toml``, its drawing code, theme, assets and outputs.

``svgwriter new NAME --preset poster`` starts one from a preset, ``svgwriter build`` writes its outputs and
``svgwriter preview`` shows them in a browser that reloads on every save. In Python, :class:`Project` does
the same: ``svg.Project.load().build()``. Presets are a registry (:data:`presets`).

Example
-------
>>> import svgwriter as svg, tempfile
>>> with tempfile.TemporaryDirectory() as folder:
...     project = svg.Project.new(f"{folder}/poster", preset="poster")
...     print(project.config.size, [path.suffix for path in project.build(["svg", "png"])])
a4 ['.svg', '.png']
"""

from __future__ import annotations

from ._config import ProjectConfig
from ._gallery import Preview
from ._presets import Preset, ProjectPresets, presets
from .project import Project

__all__ = [
    "presets",
    "Preset",
    "Preview",
    "Project",
    "ProjectConfig",
    "ProjectPresets",
]
