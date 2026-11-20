from collections.abc import AsyncIterator, Mapping
from typing import Any
from .._internal._typing import AnyPath
from ..elements.core._element import Element
from .writer import SerializeOptions

__all__ = ["aiter_chunks", "write_async", "write_many_async"]

async def write_async(
    element: Element,
    path: AnyPath,
    **kwargs: Any,
) -> None: ...

async def write_many_async(targets: Mapping[AnyPath, Element], **kwargs: Any) -> int: ...

def aiter_chunks(
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
) -> AsyncIterator[str]: ...
