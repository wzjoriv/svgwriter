"""
``Project``: a design folder with a manifest, built into its outputs, previewed in notebooks or a browser.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from ..video import Scene
from ..widgets import Control, controls_of
from ._build import write_outputs
from ._config import ProjectConfig, check_formats, read_config
from ._constants import DEFAULT_PORT, NOTEBOOK_SUFFIX
from ._entry import (
    entry_parts,
    items_of,
    load_object,
    load_theme,
    project_scope,
    register_fonts,
    working_directory,
)
from ._gallery import Preview
from ._notebook import headless, kernel_object, run_notebook
from .presets import create

__all__ = ["Project"]


class Project:
    """A design project: a folder with ``svgwriter.toml``, the code that draws it and the files it builds.

    The manifest names the entry (``"main:build"``, a function that draws into a document of the project's
    size and theme), the theme file and the output formats. ``[tool.svgwriter]`` in ``pyproject.toml`` works
    as well, with the same keys. Nothing is read implicitly: importing svgwriter or creating a document never
    looks for a manifest; only :meth:`load` and the ``svgwriter build`` and ``svgwriter preview`` commands do.

    Parameters
    ----------
    config : ProjectConfig
        The settings, usually from :meth:`load`.

    See Also
    --------
    svgwriter.project.register_preset : Add a starter folder for :meth:`new`.

    Notes
    -----
    The entry may be a function taking a :class:`~svgwriter.Document`, a :class:`~svgwriter.Scene` class, or a
    list of either (one slide or page each), and may live in a notebook (``"main.ipynb:build"``). Modules the
    project imports, and the animations and sizes they register, are forgotten after each build, so a build
    always runs the current files.

    Examples
    --------
    >>> import svgwriter as svg, tempfile
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     project = svg.Project.new(f"{folder}/card", preset="blank")
    ...     print([path.name for path in project.build()])
    ['card.svg', 'card.png']
    """

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config

    def __repr__(self) -> str:
        return f"<Project {self.name!r} at {self.root}>"

    @classmethod
    def load(cls, path: str | os.PathLike[str] = ".") -> Project:
        """Read the project whose manifest is in *path* or the nearest folder above it.

        ``svgwriter.toml`` comes first; otherwise a ``pyproject.toml`` with a ``[tool.svgwriter]`` table.

        Parameters
        ----------
        path : str or os.PathLike, optional
            Where to start looking. Defaults to the current folder.

        Returns
        -------
        Project
            The project.

        Raises
        ------
        ProjectError
            If no manifest is found, or it has an unknown key or a bad value (the message names the file and key).

        Examples
        --------
        >>> import svgwriter as svg, tempfile, pathlib
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     _ = pathlib.Path(folder, "svgwriter.toml").write_text('[project]\\nname = "demo"\\nsize = "a4"')
        ...     print(svg.Project.load(folder).config.size)
        a4
        """
        return cls(read_config(Path(path)))

    @classmethod
    def new(cls, path: str | os.PathLike[str], preset: str = "blank", *, notebook: bool = False,
            name: str | None = None) -> Project:
        """Create a project folder from a preset and load it.

        Parameters
        ----------
        path : str or os.PathLike
            The new folder; it must not exist or be empty.
        preset : str, optional
            A name from :data:`svgwriter.project.PRESETS`. Defaults to ``"blank"``.
        notebook : bool, optional
            Write ``main.ipynb`` instead of ``main.py``. Defaults to False.
        name : str, optional
            The project name. Defaults to the folder name.

        Returns
        -------
        Project
            The new project, ready to build.

        Raises
        ------
        ProjectError
            If the preset is unknown (the message lists the presets) or the folder is not empty.

        Examples
        --------
        >>> import svgwriter as svg, tempfile
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     print(svg.Project.new(f"{folder}/talk", preset="slides").config.formats)
        ('pptx', 'pdf')
        """
        return cls.load(create(path, preset, notebook=notebook, name=name))

    @property
    def root(self) -> Path:
        """The project folder."""
        return self.config.root

    @property
    def name(self) -> str:
        """The project name; output files are named after it."""
        return self.config.name

    @property
    def output(self) -> Path:
        """The folder the outputs are written to."""
        return self.root / self.config.output

    def build(self, formats: Sequence[str] | None = None, *, values: Mapping[str, Any] | None = None) -> list[Path]:
        """Draw the project and write its outputs into the output folder.

        Fonts in the font folder are registered first, the theme applies to every page and scene (also to
        scenes the entry module makes when it is imported), and the project's code runs in the project folder, so relative paths such as ``assets/data/values.csv`` work.

        Parameters
        ----------
        formats : sequence of str, optional
            Formats to write. Defaults to None, the ``[outputs] formats`` of the manifest.
        values : mapping, optional
            Values for the controls the entry declares (:func:`svgwriter.widgets.controls`), by parameter
            name. Defaults to None, their starting values.

        Returns
        -------
        list of pathlib.Path
            The files written, in format order.

        Raises
        ------
        ProjectError
            If the entry, the theme or a format cannot be found.

        Notes
        -----
        With a notebook entry, a call from inside that notebook uses the notebook's own entry object; any other
        call runs the notebook in a new kernel (the ``notebook`` extra) and builds there, so both write the same
        files.

        Examples
        --------
        >>> import svgwriter as svg, tempfile
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     project = svg.Project.new(f"{folder}/sheet", preset="poster")
        ...     print([path.name for path in project.build(["svg"])])
        ['sheet.svg']
        """
        if headless():
            return []
        chosen = check_formats("formats", formats) if formats is not None else self.config.formats
        register_fonts(self.config)
        theme = load_theme(self.config)
        target, attribute = entry_parts(self.config)
        if target.endswith(NOTEBOOK_SUFFIX):
            value = kernel_object(attribute)
            if value is None:
                return run_notebook(self.config, self.root / target, chosen)
            with working_directory(self.root):
                return write_outputs(self.config, items_of(self.config, value), theme, chosen, values)
        with project_scope(self.root), working_directory(self.root):
            with theme if theme is not None else nullcontext():
                entry = load_object(self.config)
            return write_outputs(self.config, items_of(self.config, entry), theme, chosen, values)

    def controls(self) -> dict[str, Control]:
        """The controls the entry's page functions declare with :func:`svgwriter.widgets.controls`.

        ``svgwriter preview`` shows them as a form above the outputs; ``svgwriter build`` uses their starting
        values. Notebook entries declare none here.

        Returns
        -------
        dict of str to Control
            One control per parameter name, across the entry's functions.

        Raises
        ------
        ProjectError
            If the entry cannot be found.

        Examples
        --------
        >>> import svgwriter as svg, tempfile
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     print(svg.Project.new(f"{folder}/card").controls())
        {}
        """
        if entry_parts(self.config)[0].endswith(NOTEBOOK_SUFFIX):
            return {}
        found: dict[str, Control] = {}
        with project_scope(self.root), working_directory(self.root):
            for item in items_of(self.config, load_object(self.config)):
                if not isinstance(item, (Scene, type)):
                    found.update(controls_of(item, infer=False))
        return found

    def preview(self, formats: Sequence[str] | None = None) -> Preview:
        """Build the outputs and show them: in a notebook each file appears inline, and animations play.

        Parameters
        ----------
        formats : sequence of str, optional
            Formats to build and show. Defaults to the manifest's.

        Returns
        -------
        Preview
            Displays as HTML in notebooks; ``preview.paths`` lists the files.

        See Also
        --------
        serve : A browser page that rebuilds on every save.

        Examples
        --------
        >>> import svgwriter as svg, tempfile
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     shown = svg.Project.new(f"{folder}/card").preview(["svg"])
        ...     print("<img" in shown._repr_html_())
        True
        """
        return Preview(self.build(formats), self.name)

    def serve(self, port: int = DEFAULT_PORT, *, open_browser: bool = True) -> None:
        """Serve a live preview at ``http://127.0.0.1:<port>`` until interrupted (Ctrl+C).

        The project is rebuilt whenever one of its files changes, and the page reloads itself; a failed build
        shows its traceback under the last outputs that worked. Controls the entry declares
        (:func:`svgwriter.widgets.controls`) appear as a form above the outputs, which rebuild as they change.

        Parameters
        ----------
        port : int, optional
            The local port. Defaults to 8000.
        open_browser : bool, optional
            Open the page in the default browser. Defaults to True.

        See Also
        --------
        preview : The same outputs inline in a notebook.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Project.load().serve()  # doctest: +SKIP
        """
        from ._server import LiveServer

        LiveServer(self.root, lambda values: Project.load(self.root).build(values=values), self.name, port,
                   controls=lambda: Project.load(self.root).controls()).serve(open_browser)
