import numpy as np
from collections.abc import Iterable
from typing import Any
from numpy import float32
from ..document import Document

__all__ = ["rasterize_many"]

def rasterize_many(
    documents: Iterable[Document],
    *,
    processes: int | None = None,
    dtype: Any = float32,
    **options: Any,
) -> list[np.ndarray]: ...
