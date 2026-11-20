"""
The exporter and importer registries, discoverable by format name or file extension.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from ..document import Document

__all__ = [
    "Exporter",
    "Importer",
    "exporters",
    "find_exporter",
    "find_importer",
    "importers",
    "register",
    "register_importer",
    "unregister",
]

ExportFunction = Callable[..., "bytes | str"]
ImportFunction = Callable[..., "Document"]
F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class Exporter:
    """A registered output format.

    Attributes
    ----------
    name : str
        Lower-case format name.
    function : callable
        ``function(document, **options)`` returning ``bytes`` or ``str``.
    extensions : tuple of str
        File extensions, lower-case with a leading dot.
    binary : bool
        Whether the function returns ``bytes``.
    description : str
        First docstring line of the function.

    See Also
    --------
    register : Register an exporter.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.exporters()["png"].binary
    True
    """

    name: str
    function: ExportFunction
    extensions: tuple[str, ...] = ()
    binary: bool = True
    description: str = ""


@dataclass(frozen=True)
class Importer:
    """A registered input format.

    Attributes
    ----------
    name : str
        Lower-case format name.
    function : callable
        ``function(data: bytes, **options)`` returning a :class:`~svgwriter.Document`.
    extensions : tuple of str
        File extensions, lower-case with a leading dot.
    description : str
        First docstring line of the function.

    See Also
    --------
    register_importer : Register an importer.

    Examples
    --------
    >>> import svgwriter as svg
    >>> ".svg" in svg.export.importers()["svg"].extensions
    True
    """

    name: str
    function: ImportFunction
    extensions: tuple[str, ...] = ()
    description: str = field(default="")


_EXPORTERS: dict[str, Exporter] = {}
_IMPORTERS: dict[str, Importer] = {}


def _extensions(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(e.lower() if e.startswith(".") else "." + e.lower() for e in values)


def register(
    name: str, *, extensions: tuple[str, ...] = (), binary: bool = True, replace: bool = False
) -> Callable[[F], F]:
    """Decorator registering an exporter ``function(document, **options) -> bytes | str``.

    Parameters
    ----------
    name : str
        Format name used by :func:`export` and :meth:`Document.export`.
    extensions : tuple of str, optional
        File extensions (``".pdf"``) that select this format in :func:`save`. Defaults to ().
    binary : bool, optional
        Whether the function returns ``bytes`` (otherwise ``str``). Defaults to True.
    replace : bool, optional
        Allow replacing an existing registration of *name*. Defaults to False.

    Returns
    -------
    callable
        A decorator that registers the function and returns it unchanged.

    Raises
    ------
    ValueError
        If *name* is already registered and *replace* is false.

    See Also
    --------
    register_importer : Register an input format.
    unregister : Remove a registration.

    Notes
    -----
    Third-party packages can register formats on import; the first line of
    the function's docstring becomes its description in :func:`exporters`.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.export.register("count", extensions=(".count",), binary=False, replace=True)
    ... def count(document, **options):
    ...     return str(len(document))
    >>> svg.export.export(svg.Document(), "count")
    '0'
    >>> svg.export.unregister("count")
    """

    def decorate(function: F) -> F:
        key = name.lower()
        if key in _EXPORTERS and not replace:
            raise ValueError(f"exporter {name!r} is already registered; pass replace=True to override")
        doc = (function.__doc__ or "").strip().splitlines()
        _EXPORTERS[key] = Exporter(key, function, _extensions(extensions), binary, doc[0] if doc else "")
        return function

    return decorate


def unregister(name: str, *, importer: bool = False) -> None:
    """Remove a registered exporter (or importer, with *importer*).

    Undoes a :func:`register` or :func:`register_importer` call, for instance to keep
    examples and tests from leaking global state.

    Parameters
    ----------
    name : str
        The format name given to :func:`register` or :func:`register_importer`.
    importer : bool, optional
        Remove the importer instead of the exporter. Defaults to False.

    Raises
    ------
    KeyError
        When nothing is registered under *name*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> _ = svg.export.register("tmp", replace=True)(lambda document, **options: b"")
    >>> svg.export.unregister("tmp")
    >>> "tmp" in svg.export.exporters()
    False
    """
    registry = _IMPORTERS if importer else _EXPORTERS
    try:
        del registry[name.lower()]
    except KeyError:
        raise KeyError(f"no {'importer' if importer else 'exporter'} named {name!r}") from None


def register_importer(name: str, *, extensions: tuple[str, ...] = (), replace: bool = False) -> Callable[[F], F]:
    """Decorator registering an importer ``function(data: bytes, **options) -> Document``.

    Parameters
    ----------
    name : str
        Format name used by :func:`load`.
    extensions : tuple of str, optional
        File extensions (``".svg"``) that select this format. Defaults to ().
    replace : bool, optional
        Allow replacing an existing registration of *name*. Defaults to False.

    Returns
    -------
    callable
        A decorator that registers the function and returns it unchanged.

    Raises
    ------
    ValueError
        If *name* is already registered and *replace* is false.

    See Also
    --------
    register : Register an output format.
    unregister : Remove a registration.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.export.register_importer("blank", extensions=(".blank",), replace=True)
    ... def read_blank(data, **options):
    ...     return svg.Document(1, 1)
    >>> svg.export.find_importer("x.blank").name
    'blank'
    >>> svg.export.unregister("blank", importer=True)
    """

    def decorate(function: F) -> F:
        key = name.lower()
        if key in _IMPORTERS and not replace:
            raise ValueError(f"importer {name!r} is already registered; pass replace=True to override")
        doc = (function.__doc__ or "").strip().splitlines()
        _IMPORTERS[key] = Importer(key, function, _extensions(extensions), doc[0] if doc else "")
        return function

    return decorate


def exporters() -> dict[str, Exporter]:
    """Registered exporters by name.

    Returns
    -------
    dict of str to Exporter
        A copy of the registry, built-in formats included.

    See Also
    --------
    importers : The input formats.

    Examples
    --------
    >>> import svgwriter as svg
    >>> {"svg", "png", "pdf"} <= set(svg.export.exporters())
    True
    """
    _load_builtins()
    return dict(_EXPORTERS)


def importers() -> dict[str, Importer]:
    """Registered importers by name.

    Returns
    -------
    dict of str to Importer
        A copy of the registry, built-in formats included.

    See Also
    --------
    exporters : The output formats.

    Examples
    --------
    >>> import svgwriter as svg
    >>> {"svg", "image"} <= set(svg.export.importers())
    True
    """
    _load_builtins()
    return dict(_IMPORTERS)


def _find(registry: dict[str, Any], key: str | os.PathLike[str], kind: str) -> Any:
    _load_builtins()
    text = os.fspath(key)
    lowered = text.lower()
    if lowered in registry:
        return registry[lowered]
    suffix = "".join(Path(lowered).suffixes[-1:]) if not lowered.startswith(".") else lowered
    for item in registry.values():
        if suffix in item.extensions:
            return item
    known = ", ".join(sorted(e for item in registry.values() for e in item.extensions))
    raise ValueError(f"no {kind} for {text!r}; known extensions: {known}")


def find_exporter(key: str | os.PathLike[str]) -> Exporter:
    """The exporter for a format name, an extension (``".pdf"``) or a file path.

    Parameters
    ----------
    key : str or path-like
        A registered name, an extension, or a path whose extension selects the format.

    Returns
    -------
    Exporter
        The matching registration.

    Raises
    ------
    ValueError
        If nothing matches.

    See Also
    --------
    find_importer : The input-side lookup.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.find_exporter("drawing.pdf").name
    'pdf'
    """
    return _find(_EXPORTERS, key, "exporter")


def find_importer(key: str | os.PathLike[str]) -> Importer:
    """The importer for a format name, an extension or a file path.

    Parameters
    ----------
    key : str or path-like
        A registered name, an extension, or a path whose extension selects the format.

    Returns
    -------
    Importer
        The matching registration.

    Raises
    ------
    ValueError
        If nothing matches.

    See Also
    --------
    find_exporter : The output-side lookup.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.export.find_importer("drawing.svgz").name
    'svg'
    """
    return _find(_IMPORTERS, key, "importer")


def _load_builtins() -> None:
    from . import _diagram, _html, _office, _plotter, _raster, _scene, _svg, _text, _vector  # noqa: F401
