from ...document import Document

__all__ = ["read_d2", "read_dot", "read_mermaid", "read_plantuml"]

def read_dot(
    data: bytes,
    *,
    engine: str = 'dot',
) -> Document: ...

def read_mermaid(
    data: bytes,
    *,
    theme: str = 'default',
) -> Document: ...

def read_plantuml(data: bytes) -> Document: ...

def read_d2(data: bytes) -> Document: ...
