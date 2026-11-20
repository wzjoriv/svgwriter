from ...document import Document

__all__ = ["to_tikz"]

def to_tikz(
    document: Document,
    *,
    standalone: bool = False,
    text: bool = True,
) -> str: ...
