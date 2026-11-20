"""
Rendering many documents at once in worker processes (skia holds the GIL, so threads do not help).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any

import numpy as np

from ._constants import CHANNEL_SCALE, SERIAL_LIMIT

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["rasterize_many"]


def _render(job: tuple[str, str | None, dict[str, Any], bool]) -> np.ndarray:
    """Worker: parse one document's SVG text and rasterize it (as uint8 when asked, to send less data back)."""
    from ..document import Document

    text, source, options, small = job
    document = Document.from_string(text)
    if source is not None:
        document.root.__dict__["_source_path"] = source
    pixels = document.rasterize(**options)
    return np.clip(np.rint(pixels * CHANNEL_SCALE), 0, CHANNEL_SCALE).astype(np.uint8) if small else pixels


def rasterize_many(documents: Iterable[Document], *, processes: int | None = None, dtype: Any = np.float32,
                   **options: Any) -> list[np.ndarray]:
    """Rasterize several documents in parallel worker processes.

    Each document travels to a worker as SVG text, so anything the SVG keeps
    renders the same as ``document.rasterize(**options)``; linked files are
    resolved against each document's source path.

    Parameters
    ----------
    documents : iterable of Document
        The drawings (frames of an animation, a batch of icons, ...).
    processes : int, optional
        Worker count. Defaults to None (one per CPU); ``1`` renders in this process.
    dtype : numpy dtype, optional
        ``numpy.float32`` (0..1, like ``rasterize``) or ``numpy.uint8`` (0..255,
        four times less data to move between processes). Defaults to float32.
    **options
        ``scale``, ``size``, ``padding``, ``background`` as for :meth:`Document.rasterize`.

    Returns
    -------
    list of numpy.ndarray
        ``float32`` RGBA arrays in the order of *documents*.

    Notes
    -----
    Start-up costs a fraction of a second, so pools pay off from a few
    dozen non-trivial documents; small batches run in this process. Scripts
    that use this on Windows or macOS need the usual
    ``if __name__ == "__main__":`` guard.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops import rasterize_many
    >>> frames = [svg.Document(4, 4) for _ in range(2)]
    >>> [a.shape for a in rasterize_many(frames, processes=1)]
    [(4, 4, 4), (4, 4, 4)]
    """
    small = np.dtype(dtype) == np.uint8
    jobs = [(document.to_string(), document.root.__dict__.get("_source_path"), options, small)
            for document in documents]
    workers = processes if processes is not None else os.cpu_count() or 1
    if workers <= 1 or len(jobs) <= SERIAL_LIMIT:
        return [_render(job) for job in jobs]
    with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
        return list(pool.map(_render, jobs, chunksize=max(len(jobs) // (workers * 4), 1)))
