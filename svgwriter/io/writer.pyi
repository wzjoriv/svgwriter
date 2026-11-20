from collections.abc import Iterator
from dataclasses import InitVar, dataclass
from typing import Any
from .._internal._sentinels import MissingType
from .._internal._typing import AnyPath
from ..attributes.protocols import TextSink
from ..elements.core import Element

__all__ = ["SerializeOptions", "Writer", "iter_chunks", "to_string", "write"]

@dataclass(kw_only=True)
class SerializeOptions:
    pretty: InitVar[bool] = True
    indent: str = '  '
    precision: int = 4
    xml_declaration: bool = True
    doctype: bool = False
    encoding: str = 'utf-8'
    compact_paths: bool = False
    namespaces: dict[str, str] = ...
    newline: str = '\n'

    def __init__(
        self,
        *,
        pretty: bool = True,
        indent: str = '  ',
        precision: int = 4,
        xml_declaration: bool = True,
        doctype: bool = False,
        encoding: str = 'utf-8',
        compact_paths: bool = False,
        namespaces: dict[str, str] = ...,
    ) -> None: ...
    def __post_init__(self, pretty: bool) -> None: ...

class Writer:
    options: Any

    def __init__(
        self,
        options: SerializeOptions | None = None,
        *,
        pretty: bool = True,
        indent: str = '  ',
        precision: int = 4,
        xml_declaration: bool = True,
        doctype: bool = False,
        encoding: str = 'utf-8',
        compact_paths: bool = False,
        namespaces: dict[str, str] = ...,
    ) -> None: ...
    def iter_chunks(
        self,
        element: Element,
        *,
        xml_declaration: bool | MissingType = MissingType.MISSING,
    ) -> Iterator[str]: ...
    def to_string(
        self,
        element: Element,
        *,
        xml_declaration: bool | MissingType = MissingType.MISSING,
    ) -> str: ...
    def write(
        self,
        element: Element,
        target: AnyPath | TextSink,
        *,
        xml_declaration: bool | MissingType = MissingType.MISSING,
    ) -> None: ...

def iter_chunks(
    element: Element,
    *,
    xml_declaration: bool = True,
    options: SerializeOptions | None = None,
    pretty: bool = True,
    indent: str = '  ',
    precision: int = 4,
    doctype: bool = False,
    encoding: str = 'utf-8',
    compact_paths: bool = False,
    namespaces: dict[str, str] = ...,
) -> Iterator[str]: ...

def to_string(
    element: Element,
    *,
    options: SerializeOptions | None = None,
    pretty: bool = True,
    indent: str = '  ',
    precision: int = 4,
    xml_declaration: bool = True,
    doctype: bool = False,
    encoding: str = 'utf-8',
    compact_paths: bool = False,
    namespaces: dict[str, str] = ...,
) -> str: ...

def write(
    element: Element,
    target: AnyPath | TextSink,
    *,
    options=None,
    pretty: bool = True,
    indent: str = '  ',
    precision: int = 4,
    xml_declaration: bool = True,
    doctype: bool = False,
    encoding: str = 'utf-8',
    compact_paths: bool = False,
    namespaces: dict[str, str] = ...,
) -> None: ...
