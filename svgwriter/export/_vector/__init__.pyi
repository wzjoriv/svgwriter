from ...document import Document as Document
from .._registry import register as register, register_importer as register_importer

def pdf(
    document: Document,
    *,
    title: str | None = None,
    author: str | None = None,
    text: bool = True,
) -> bytes: ...

def tikz(
    document: Document,
    *,
    standalone: bool = False,
    text: bool = True,
) -> str: ...

def eps(
    document: Document,
    *,
    text: bool = True,
) -> bytes: ...

def read_pdf(
    data: bytes,
    *,
    page: int = 0,
) -> Document: ...

def read_tikz(data: bytes) -> Document: ...

def read_eps(data: bytes) -> Document: ...
