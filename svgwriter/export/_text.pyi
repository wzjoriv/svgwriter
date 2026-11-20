from ..document import Document

__all__ = ["read_markdown", "read_text"]

def read_text(data: bytes) -> Document: ...

def read_markdown(data: bytes) -> Document: ...
