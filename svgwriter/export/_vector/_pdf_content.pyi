from typing import Any, Final
from ._pdf_read import _Painter

__all__ = ["CONTENT_HANDLERS", "draw_image"]

def draw_image(painter: _Painter, stream: Any) -> None: ...

CONTENT_HANDLERS: Final = ...
