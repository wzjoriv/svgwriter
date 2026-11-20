from ...document import Document

__all__ = ["to_eps"]

def to_eps(
    document: Document,
    *,
    text: bool = True,
) -> str: ...
