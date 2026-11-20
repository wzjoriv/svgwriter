from ...document import Document

__all__ = ["read_pdf"]

def read_pdf(
    data: bytes,
    *,
    page: int = 0,
) -> Document: ...
