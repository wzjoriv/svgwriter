from ...document import Document
from ...elements.structure import Group

__all__ = ["DiagramToolError", "latex", "read_d2", "read_dot", "read_mermaid", "read_plantuml"]

class DiagramToolError(RuntimeError):
    ...

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

def latex(
    source: str,
    *,
    display: bool = False,
    preamble: str = '',
) -> Group: ...

def read_plantuml(data: bytes) -> Document: ...

def read_d2(data: bytes) -> Document: ...
