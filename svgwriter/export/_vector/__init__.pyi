from collections.abc import Sequence
from ...document import Document as Document
from .._registry import register as register, register_importer as register_importer
from ._constants import PDF_LINK_KEY as PDF_LINK_KEY

def pdf(
    document: Document | Sequence[Document],
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
    page: int | None = 0,
) -> Document | list[Document]: ...

def read_tikz(data: bytes) -> Document: ...

def read_eps(data: bytes) -> Document: ...
