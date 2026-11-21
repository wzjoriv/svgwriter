"""Every error svgwriter raises on purpose, in one place: ``svg.errors.<Name>``.

Each subclasses the built-in exception a caller would expect (``ValueError`` for bad values, ``KeyError``
for failed lookups, ``AttributeError`` and ``TypeError`` for misspelled names), so ``except ValueError``
keeps working.

Examples
--------
>>> import svgwriter as svg
>>> try:
...     svg.themes.get("drak")
... except svg.errors.UnknownNameError as error:
...     print(type(error).__module__, error)
svgwriter.errors unknown theme 'drak'; did you mean 'dark'?
"""

from __future__ import annotations

from ._internal._errors import (
    DiagramToolError,
    FFmpegError,
    FFmpegNotFoundError,
    OfficeExtraError,
    PathSyntaxError,
    ProjectError,
    SceneError,
    SVGParseError,
    ThemeError,
    UnknownAttributeError,
    UnknownKeywordError,
    UnknownNameError,
)

__all__ = [
    "DiagramToolError",
    "FFmpegError",
    "FFmpegNotFoundError",
    "OfficeExtraError",
    "PathSyntaxError",
    "ProjectError",
    "SVGParseError",
    "SceneError",
    "ThemeError",
    "UnknownAttributeError",
    "UnknownKeywordError",
    "UnknownNameError",
]
