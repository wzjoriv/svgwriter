import os
from collections.abc import Callable
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, TypeAlias, TypeVar
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

ExportFunction: TypeAlias = Callable[..., bytes | str]
ImportFunction: TypeAlias = Callable[..., Document]
F = TypeVar('F', bound=Callable[..., Any])

@dataclass(frozen=True)
class Exporter:
    name: str
    function: ExportFunction
    extensions: tuple[str, ...] = ()
    binary: bool = True
    description: str = ''

    def __init__(
        self,
        name: str,
        function: Callable[..., bytes | str],
        extensions: tuple[str, ...] = (),
        binary: bool = True,
        description: str = '',
    ) -> None: ...

@dataclass(frozen=True)
class Importer:
    name: str
    function: ImportFunction
    extensions: tuple[str, ...] = ()
    description: str = ''

    def __init__(
        self,
        name: str,
        function: ImportFunction,
        extensions: tuple[str, ...] = (),
        description: str = '',
    ) -> None: ...

def register(
    name: str,
    *,
    extensions: tuple[str, ...] = (),
    binary: bool = True,
    replace: bool = False,
) -> Callable[[F], F]: ...

def unregister(
    name: str,
    *,
    importer: bool = False,
) -> None: ...

def register_importer(
    name: str,
    *,
    extensions: tuple[str, ...] = (),
    replace: bool = False,
) -> Callable[[F], F]: ...

def exporters() -> dict[str, Exporter]: ...

def importers() -> dict[str, Importer]: ...

def find_exporter(key: str | PathLike[str]) -> Exporter: ...

def find_importer(key: str | PathLike[str]) -> Importer: ...

def export(
    document: Document,
    format: str,
    *,
    time: float | None = None,
    **options: Any,
) -> bytes | str: ...

def save(
    document: Document,
    path: str | os.PathLike[str],
    format: str | None = None,
    *,
    time: float | None = None,
    **options: Any,
) -> Path: ...

def load(
    path: str | os.PathLike[str],
    format: str | None = None,
    **options: Any,
) -> Document: ...
