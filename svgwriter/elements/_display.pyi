from .._internal._typing import AnyPath
from ..attributes.protocols import TextSink
from ..io.writer import SerializeOptions

class Displayable:
    def to_string(
        self,
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
    def save(
        self,
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
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
