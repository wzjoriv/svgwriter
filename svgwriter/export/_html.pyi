from collections.abc import Mapping
from ..document import Document

__all__ = ["html_page", "read_html"]

def html_page(
    document: Document,
    *,
    title: str | None = None,
    background: str = 'white',
    css: str = '',
    handlers: Mapping[str, Mapping[str, str]] | None = None,
) -> str: ...

def read_html(data: bytes) -> Document: ...
