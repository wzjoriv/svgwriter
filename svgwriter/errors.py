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

import difflib

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


class UnknownNameError(KeyError, ValueError):
    """A name that no registry entry has; the message suggests the closest names.

    It is both a ``KeyError`` (a failed lookup) and a ``ValueError`` (a bad argument value), so either
    ``except`` catches it.

    Examples
    --------
    >>> import svgwriter as svg
    >>> isinstance(svg.errors.UnknownNameError("x"), (KeyError, ValueError))
    True
    """

    def __str__(self) -> str:
        return str(self.args[0]) if self.args else ""


class UnknownAttributeError(AttributeError):
    """An attribute that is neither a Python member nor a known SVG attribute.

    The "did you mean" suggestion is computed only when the message is shown,
    so ``getattr(element, name, default)`` stays cheap.

    Parameters
    ----------
    owner : str
        The class name of the element.
    name : str
        The attribute that was requested.
    members : type, optional
        The class whose public members are suggested too. Defaults to None.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.rect(0, 0, 1, 1).widht
    ... except AttributeError as error:
    ...     print("did you mean 'width'?" in str(error))
    True
    >>> try:
    ...     svg.text("A").fade_out()
    ... except AttributeError as error:
    ...     print(str(error).split(": ", 1)[1])
    fade_out is an animation; use element.animate.fade_out(...)
    """

    def __init__(self, owner: str, name: str, members: type | None = None) -> None:
        super().__init__(name)
        self.owner = owner
        self.attribute = name
        self.members = members

    def __str__(self) -> str:
        from ._internal._constants import SUGGESTIONS
        from ._internal._presets import KINDS

        presets = {name: kind for kind in ("animation", "behavior") for name in KINDS[kind].list()}
        if self.attribute in presets:
            return (f"{self.owner} has no attribute {self.attribute!r}: {self.attribute} is "
                    f"{'an animation' if presets[self.attribute] == 'animation' else 'a behavior'}; "
                    f"use element.animate.{self.attribute}(...)")
        methods = [m for m in dir(self.members) if not m.startswith("_")] if self.members is not None else []
        hint = [m for m in methods if m.startswith(self.attribute)][:SUGGESTIONS] or difflib.get_close_matches(
            self.attribute, [*methods, *_python_names(), *presets], n=1)
        hint = [f"animate.{name}" if name in presets else name for name in hint]
        suggestion = f"; did you mean {' or '.join(map(repr, hint))}?" if hint else ""
        return (f"{self.owner} has no attribute {self.attribute!r}{suggestion} "
                "(unlisted SVG attributes: element.set(name, value))")


class UnknownKeywordError(UnknownAttributeError, TypeError):
    """An unknown keyword argument (likely a typo); custom attributes go in ``attrs={...}``.

    Parameters
    ----------
    owner : str
        The class name of the element.
    name : str
        The keyword that was given.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.rect(0, 0, 1, 1, widht=3)
    ... except TypeError as error:
    ...     print(type(error).__name__)
    UnknownKeywordError
    """

    def __str__(self) -> str:
        hint = difflib.get_close_matches(self.attribute, _python_names(), n=1)
        suggestion = f"; did you mean {hint[0]!r}?" if hint else ""
        return (f"{self.owner}() got an unknown attribute keyword {self.attribute!r}{suggestion} "
                "(custom attributes: attrs={...} or data_* keywords)")


def _python_names() -> list[str]:
    from .model.attributes.names import KNOWN_ATTRIBUTES, py_name

    return sorted({py_name(name) for name in KNOWN_ATTRIBUTES})


class SVGParseError(ValueError):
    """Malformed SVG input or, when strict, unsupported content.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.parse("<svg")
    ... except svg.errors.SVGParseError:
    ...     print("malformed")
    malformed
    """


class PathSyntaxError(ValueError):
    """Malformed path data; records where in the text parsing failed.

    Parameters
    ----------
    message : str
        What went wrong.
    position : int
        Character offset of the error; also stored as the ``position`` attribute.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.PathData("L1 1")
    ... except svg.errors.PathSyntaxError as error:
    ...     print(error)
    path data must start with a moveto at offset 0
    """

    def __init__(self, message: str, position: int) -> None:
        super().__init__(f"{message} at offset {position}")
        self.position = position


class ThemeError(ValueError):
    """A theme that cannot be resolved: an unknown role or reference, a cycle, or a malformed value.

    Examples
    --------
    >>> import svgwriter as svg
    >>> try:
    ...     svg.theme.Palette({"a": "{palette.b}"})
    ... except svg.errors.ThemeError as error:
    ...     print(error)
    palette.a: unknown reference {palette.b}
    """


class SceneError(ValueError):
    """A source defines no scene, or no scene with a requested name.

    Examples
    --------
    >>> import svgwriter as svg
    >>> issubclass(svg.errors.SceneError, ValueError)
    True
    """


class FFmpegNotFoundError(RuntimeError):
    """``ffmpeg`` is not installed or not on ``PATH``."""


class FFmpegError(RuntimeError):
    """``ffmpeg`` ran but failed; the message carries the exit status and the tail of its error output."""


class ProjectError(ValueError):
    """A project file is missing or invalid, or its entry cannot be loaded; the message names the file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> issubclass(svg.errors.ProjectError, ValueError)
    True
    """


class DiagramToolError(RuntimeError):
    """A diagram tool (Graphviz, Mermaid, PlantUML, D2, LaTeX) is missing or rejected the input."""


class OfficeExtraError(ImportError):
    """The library for an Office format is not installed (``pip install "pysvgwriter[office]"``)."""
