from ...document import Document as Document
from .._registry import register as register, register_importer as register_importer

def excalidraw(
    document: Document,
    *,
    seed: int = 0,
) -> str: ...

def read_excalidraw(data: bytes) -> Document: ...
