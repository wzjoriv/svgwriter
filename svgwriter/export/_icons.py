"""
Icon containers: Windows ``.ico`` and macOS ``.icns``, both holding PNG images.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["ICNS_SIZES", "ICO_SIZES", "read_icon", "to_icns", "to_ico"]

ICO_SIZES: Final = (16, 24, 32, 48, 64, 128, 256)
ICNS_SIZES: Final = (16, 32, 64, 128, 256, 512, 1024)
ICO_MAX: Final = 256
ICO_HEADER: Final = struct.Struct("<HHH")
ICO_ENTRY: Final = struct.Struct("<BBBBHHII")
ICNS_HEADER: Final = struct.Struct(">4sI")
ICNS_TYPES: Final = {16: (b"icp4",), 32: (b"icp5", b"ic11"), 64: (b"icp6", b"ic12"), 128: (b"ic07",),
                     256: (b"ic08", b"ic13"), 512: (b"ic09", b"ic14"), 1024: (b"ic10",)}
PNG_MAGIC: Final = bytes.fromhex("89504e470d0a1a0a")
BITS_PER_PIXEL: Final = 32


def _pngs(document: Document, sizes: Iterable[int], padding: float) -> dict[int, bytes]:
    from ..ops.render import encode_image

    return {size: encode_image(document.rasterize(size=(size, size), padding=padding, snapshot=True))
            for size in sorted(set(sizes))}


def to_ico(document: Document, *, sizes: Iterable[int] = ICO_SIZES, padding: float = 0.0) -> bytes:
    """A Windows icon with one square PNG per size (Vista and later).

    Parameters
    ----------
    document : Document
        The drawing to rasterize at each size.
    sizes : iterable of int, optional
        Pixel sizes, each at most 256. Defaults to (16, 24, 32, 48, 64, 128, 256).
    padding : float, optional
        Margin around the drawing in its own units. Defaults to 0.0.

    Returns
    -------
    bytes
        The ICO file.

    Raises
    ------
    ValueError
        For sizes above 256 pixels, which ICO cannot hold.

    See Also
    --------
    to_icns : The macOS counterpart.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._icons import to_ico
    >>> to_ico(svg.Document(8, 8), sizes=(16, 32))[:4] == bytes.fromhex("00000100")
    True
    """
    images = _pngs(document, sizes, padding)
    if any(size > ICO_MAX or size < 1 for size in images):
        raise ValueError(f"ICO sizes must be 1..{ICO_MAX}, got {sorted(images)}")
    offset = ICO_HEADER.size + ICO_ENTRY.size * len(images)
    directory, blobs = [], []
    for size, png in images.items():
        edge = 0 if size == ICO_MAX else size
        directory.append(ICO_ENTRY.pack(edge, edge, 0, 0, 1, BITS_PER_PIXEL, len(png), offset))
        blobs.append(png)
        offset += len(png)
    return ICO_HEADER.pack(0, 1, len(images)) + b"".join(directory) + b"".join(blobs)


def to_icns(document: Document, *, sizes: Iterable[int] = ICNS_SIZES, padding: float = 0.0) -> bytes:
    """A macOS icon family: each size stored as PNG under its standard and Retina type codes.

    Parameters
    ----------
    document : Document
        The drawing to rasterize at each size.
    sizes : iterable of int, optional
        Pixel sizes from 16, 32, 64, 128, 256, 512 and 1024. Defaults to all of them.
    padding : float, optional
        Margin around the drawing in its own units. Defaults to 0.0.

    Returns
    -------
    bytes
        The ICNS file.

    Raises
    ------
    ValueError
        For sizes ICNS has no type code for.

    See Also
    --------
    to_ico : The Windows counterpart.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._icons import to_icns
    >>> to_icns(svg.Document(8, 8), sizes=(16,))[:4]
    b'icns'
    """
    unknown = [s for s in sizes if s not in ICNS_TYPES]
    if unknown:
        raise ValueError(f"ICNS sizes must be among {sorted(ICNS_TYPES)}, got {unknown}")
    chunks = []
    for size, png in _pngs(document, sizes, padding).items():
        for kind in ICNS_TYPES[size]:
            chunks.append(ICNS_HEADER.pack(kind, ICNS_HEADER.size + len(png)) + png)
    body = b"".join(chunks)
    return ICNS_HEADER.pack(b"icns", ICNS_HEADER.size + len(body)) + body


def _largest_png(data: bytes) -> bytes:
    if data[:4] == b"icns":
        best, position = b"", ICNS_HEADER.size
        while position + ICNS_HEADER.size <= len(data):
            _, length = ICNS_HEADER.unpack_from(data, position)
            payload = data[position + ICNS_HEADER.size:position + length]
            if payload.startswith(PNG_MAGIC) and len(payload) > len(best):
                best = payload
            position += max(length, ICNS_HEADER.size)
        return best
    _, kind, count = ICO_HEADER.unpack_from(data, 0)
    if kind != 1:
        raise ValueError("not an icon file")
    entries = [ICO_ENTRY.unpack_from(data, ICO_HEADER.size + i * ICO_ENTRY.size) for i in range(count)]
    width, *_, length, offset = max(entries, key=lambda e: (e[0] or ICO_MAX))
    del width
    return data[offset:offset + length]


def read_icon(data: bytes) -> Document:
    """The largest image of an ICO or ICNS file as a document (PNG-backed entries only).

    Parameters
    ----------
    data : bytes
        The icon file contents.

    Returns
    -------
    Document
        A document holding the image at its pixel size.

    Raises
    ------
    ValueError
        If the data is not an icon file or holds no PNG image.

    See Also
    --------
    to_ico : Write an ICO file.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.export._icons import read_icon, to_ico
    >>> read_icon(to_ico(svg.Document(8, 8), sizes=(16, 32))).root.view_box.width
    32
    """
    from ._builtin import read_image

    png = _largest_png(data)
    if not png:
        raise ValueError("no PNG image found in the icon file")
    return read_image(png)
