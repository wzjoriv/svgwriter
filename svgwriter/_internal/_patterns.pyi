from typing import Any
from ..document import Document
from ..transform.matrix import Matrix

__all__ = ["placed_images"]

def placed_images(document: Document) -> list[tuple[Any, Matrix]]: ...
