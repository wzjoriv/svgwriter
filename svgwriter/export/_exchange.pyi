import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from ..document import Document

__all__ = ["export", "load", "save"]

def export(
    document: Document | Sequence[Document],
    format: str,
    *,
    time: float | None = None,
    **options: Any,
) -> bytes | str: ...

def save(
    document: Document | Sequence[Document],
    path: str | os.PathLike[str],
    format: str | None = None,
    *,
    time: float | None = None,
    **options: Any,
) -> Path: ...

def load(
    path: str | os.PathLike[str],
    format: str | None = None,
    **options: Any,
) -> Document | list[Document]: ...
