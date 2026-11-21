"""
ICC profiles embedded in image files: PNG ``iCCP`` chunks and JPEG ``APP2`` segments.
"""

from __future__ import annotations

import struct
import zlib

from ._icc_constants import (
    JPEG_APP2,
    JPEG_ICC_HEADER,
    JPEG_ICC_PREFIX,
    JPEG_MARKER,
    JPEG_SEGMENT_LENGTH,
    JPEG_SOI,
    JPEG_START_OF_SCAN,
    PNG_CHUNK_OVERHEAD,
    PNG_ICC_CHUNK,
    PNG_IMAGE_DATA,
    PNG_SIGNATURE,
)

__all__ = ["embedded_profile"]


def _png_profile(data: bytes) -> bytes | None:
    position = len(PNG_SIGNATURE)
    while position + PNG_CHUNK_OVERHEAD <= len(data):
        (length,) = struct.unpack_from(">I", data, position)
        kind = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        if kind == PNG_IMAGE_DATA:
            return None
        if kind == PNG_ICC_CHUNK:
            name_end = body.find(b"\x00")
            try:
                return zlib.decompress(body[name_end + 2:]) if name_end >= 0 else None
            except zlib.error:
                return None
        position += length + PNG_CHUNK_OVERHEAD
    return None


def _jpeg_profile(data: bytes) -> bytes | None:
    parts: dict[int, bytes] = {}
    position = len(JPEG_SOI)
    while position + JPEG_SEGMENT_LENGTH + 2 <= len(data) and data[position] == JPEG_MARKER:
        marker = data[position + 1]
        if marker == JPEG_START_OF_SCAN:
            break
        (length,) = struct.unpack_from(">H", data, position + 2)
        body = data[position + 2 + JPEG_SEGMENT_LENGTH:position + 2 + length]
        if marker == JPEG_APP2 and body.startswith(JPEG_ICC_PREFIX):
            parts[body[len(JPEG_ICC_PREFIX)]] = body[JPEG_ICC_HEADER:]
        position += 2 + length
    return b"".join(parts[index] for index in sorted(parts)) or None


def embedded_profile(data: bytes) -> bytes | None:
    """The ICC profile embedded in PNG or JPEG file contents.

    Parameters
    ----------
    data : bytes
        The encoded image.

    Returns
    -------
    bytes or None
        The profile bytes, or None when the file carries none or is another format.

    Examples
    --------
    >>> from svgwriter._internal._icc_embedded import embedded_profile
    >>> embedded_profile(b"plain bytes") is None
    True
    """
    if data.startswith(PNG_SIGNATURE):
        return _png_profile(data)
    if data.startswith(JPEG_SOI):
        return _jpeg_profile(data)
    return None
