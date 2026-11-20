from ...document import Document

__all__ = ["page_count", "read_pdf"]

def read_pdf(
    data: bytes,
    *,
    page: int = 0,
) -> Document: ...

def page_count(data: bytes) -> int: ...
