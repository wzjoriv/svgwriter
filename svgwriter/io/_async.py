"""
Asynchronous wrappers around the writer.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from typing import Any

from .._internal._typing import AnyPath
from ..elements.base import Element
from ._constants import CHUNKS_PER_YIELD
from .writer import Writer, write

__all__ = ["aiter_chunks", "write_async", "write_many_async"]


async def write_async(element: Element, path: AnyPath, **kwargs: Any) -> None:
    """Write *element* to *path* in a worker thread.

    Parameters
    ----------
    element : Element
        Root of the tree to write.
    path : str or os.PathLike
        Destination file.
    **kwargs
        ``options`` or fields of :class:`~svgwriter.io.SerializeOptions`.

    See Also
    --------
    write_many_async : Write several documents concurrently.

    Examples
    --------
    >>> import asyncio, tempfile, pathlib
    >>> from svgwriter import Circle
    >>> from svgwriter.io import write_async
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     path = pathlib.Path(folder) / "a.svg"
    ...     asyncio.run(write_async(Circle(5, 5, 2), path))
    ...     print(path.read_text(encoding="utf-8").count("<circle"))
    1
    """
    await asyncio.to_thread(write, element, path, **kwargs)


async def write_many_async(targets: Mapping[AnyPath, Element], **kwargs: Any) -> int:
    """Write several documents concurrently.

    Parameters
    ----------
    targets : Mapping
        Destination path mapped to the element to write there.
    **kwargs
        ``options`` or fields of :class:`~svgwriter.io.SerializeOptions`.

    Returns
    -------
    int
        How many documents were written.

    See Also
    --------
    write_async : Write a single document.

    Examples
    --------
    >>> import asyncio, tempfile, pathlib
    >>> from svgwriter import Circle
    >>> from svgwriter.io import write_many_async
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     targets = {pathlib.Path(folder) / f"{i}.svg": Circle(i, i, 1) for i in range(3)}
    ...     print(asyncio.run(write_many_async(targets)))
    3
    """
    await asyncio.gather(*(write_async(element, path, **kwargs) for path, element in targets.items()))
    return len(targets)


async def aiter_chunks(element: Element, **kwargs: Any) -> AsyncIterator[str]:
    """Async generator of serialized chunks, yielding control periodically.

    Parameters
    ----------
    element : Element
        Root of the tree to write.
    **kwargs
        Fields of :class:`~svgwriter.io.SerializeOptions`.

    Yields
    ------
    str
        Consecutive fragments of the document.

    See Also
    --------
    svgwriter.io.iter_chunks : The synchronous equivalent.

    Examples
    --------
    >>> import asyncio
    >>> from svgwriter import Circle
    >>> from svgwriter.io import aiter_chunks
    >>> async def collect():
    ...     return [c async for c in aiter_chunks(Circle(5, 5, 2), pretty=False, xml_declaration=False)]
    >>> asyncio.run(collect())
    ['<circle cx="5" cy="5" r="2"', '/>']
    """
    for index, chunk in enumerate(Writer(**kwargs).iter_chunks(element)):
        if index % CHUNKS_PER_YIELD == 0:
            await asyncio.sleep(0)
        yield chunk
