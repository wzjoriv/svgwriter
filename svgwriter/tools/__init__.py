"""
Working with drawings: the command line, design projects and widgets.

Sub-packages
------------
cli
    The ``svgwriter`` and ``python -m svgwriter`` command line.
project
    Design projects: ``svgwriter.toml``, presets, building and live preview.
widgets
    Controls for drawing functions: notebook panels, preview forms and sweeps
    over time.

Notes
-----
The top-level package re-exports ``project`` and ``widgets``, so
``svg.Project`` and ``svg.explore`` work without this path. The group itself
imports nothing.

Examples
--------
>>> from svgwriter.tools.project import Project
>>> import svgwriter as svg
>>> Project is svg.Project
True
"""
