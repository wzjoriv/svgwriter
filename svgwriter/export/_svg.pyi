from typing import Any, Final
from ..document import Document
from ..io.parser import Strictness

GZIP_MAGIC: Final = ...

def svg_text(document: Document, **options: Any) -> str: ...

def svgz(document: Document, **options: Any) -> bytes: ...

def read_svg(
    data: bytes,
    *,
    strictness: Strictness | None = None,
) -> Document: ...
