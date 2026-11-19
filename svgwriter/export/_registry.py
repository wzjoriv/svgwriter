"""The exporter and importer registries, discoverable by format name or file extension."""

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
    "export",
    "exporters",
    "find_exporter",
    "find_importer",
    "importers",
    "load",
    "register",
    "register_importer",
    "save",
    "unregister",
]

ExportFunction = Callable[..., "bytes | str"]
ImportFunction = Callable[..., "Document"]
F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class Exporter:
    """A registered output format."""

    name: str
    function: ExportFunction
    extensions: tuple[str, ...] = ()
    binary: bool = True
    description: str = ""


@dataclass(frozen=True)
class Importer:
    """A registered input format."""

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
    extensions : tuple of str
        File extensions (``".pdf"``) that select this format in :func:`save`.
    binary : bool
        Whether the function returns ``bytes`` (otherwise ``str``).
    replace : bool
        Allow replacing an existing registration of *name*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.export.register("count", extensions=(".count",), binary=False, replace=True)
    ... def count(document, **options):
    ...     return str(len(document))
    >>> svg.export.export(svg.Document(), "count")
    '0'
    >>> svg.export.unregister("count")

    Notes
    -----
    Third-party packages can register formats on import; the first line of
    the function's docstring becomes its description in :func:`exporters`.
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
    """Decorator registering an importer ``function(data: bytes, **options) -> Document``."""

    def decorate(function: F) -> F:
        key = name.lower()
        if key in _IMPORTERS and not replace:
            raise ValueError(f"importer {name!r} is already registered; pass replace=True to override")
        doc = (function.__doc__ or "").strip().splitlines()
        _IMPORTERS[key] = Importer(key, function, _extensions(extensions), doc[0] if doc else "")
        return function

    return decorate


def exporters() -> dict[str, Exporter]:
    """Registered exporters by name."""
    _load_builtins()
    return dict(_EXPORTERS)


def importers() -> dict[str, Importer]:
    """Registered importers by name."""
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
    """The exporter for a format name, an extension (``".pdf"``) or a file path."""
    return _find(_EXPORTERS, key, "exporter")


def find_importer(key: str | os.PathLike[str]) -> Importer:
    """The importer for a format name, an extension or a file path."""
    return _find(_IMPORTERS, key, "importer")


def export(document: Document, format: str, **options: Any) -> bytes | str:
    """Convert *document* to *format* (a name or extension); returns ``bytes`` or ``str``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(4, 4)
    >>> svg.export.export(doc, "png")[:4] == bytes.fromhex("89504e47")
    True
    """
    return find_exporter(format).function(document, **options)


def save(document: Document, path: str | os.PathLike[str], format: str | None = None, **options: Any) -> Path:
    """Write *document* to *path*, choosing the format from *format* or the file extension."""
    exporter = find_exporter(format or path)
    data = exporter.function(document, **options)
    target = Path(path)
    if isinstance(data, bytes):
        target.write_bytes(data)
    else:
        target.write_text(data, encoding="utf-8", newline="\n")
    return target


def load(path: str | os.PathLike[str], format: str | None = None, **options: Any) -> Document:
    """Read a document from *path* with the importer chosen by *format* or the extension."""
    importer = find_importer(format or path)
    document = importer.function(Path(path).read_bytes(), **options)
    document.root._source_path = os.fspath(path)
    return document


def _load_builtins() -> None:
    from . import _builtin  # noqa: F401
