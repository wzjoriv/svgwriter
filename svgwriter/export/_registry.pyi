from collections.abc import Callable
from dataclasses import dataclass
from os import PathLike
from typing import Any, TypeAlias, TypeVar
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
    multipage: bool = False

    def __init__(
        self,
        name: str,
        function: Callable[..., bytes | str],
        extensions: tuple[str, ...] = (),
        binary: bool = True,
        description: str = '',
        multipage: bool = False,
    ) -> None: ...

@dataclass(frozen=True)
class Importer:
    name: str
    function: ImportFunction
    extensions: tuple[str, ...] = ()
    description: str = ''
    page_option: str | None = None

    def __init__(
        self,
        name: str,
        function: ImportFunction,
        extensions: tuple[str, ...] = (),
        description: str = '',
        page_option: str | None = None,
    ) -> None: ...

def register(
    name: str,
    *,
    extensions: tuple[str, ...] = (),
    binary: bool = True,
    multipage: bool = False,
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
    page_option: str | None = None,
    replace: bool = False,
) -> Callable[[F], F]: ...

def exporters() -> dict[str, Exporter]: ...

def importers() -> dict[str, Importer]: ...

def find_exporter(key: str | PathLike[str]) -> Exporter: ...

def find_importer(key: str | PathLike[str]) -> Importer: ...
