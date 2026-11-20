from ...document import Document

__all__ = ["read_excalidraw", "to_excalidraw"]

def read_excalidraw(text: str) -> Document: ...

def to_excalidraw(
    document: Document,
    *,
    seed: int = 0,
) -> str: ...
