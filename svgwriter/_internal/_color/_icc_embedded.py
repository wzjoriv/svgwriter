"""
ICC profiles embedded in image files: PNG ``iCCP`` chunks and JPEG ``APP2`` segments, read and written.
"""

from __future__ import annotations

import struct
import zlib

from ._icc_constants import (
    JPEG_APP0,
    JPEG_APP2,
    JPEG_ICC_CHUNK,
    JPEG_ICC_HEADER,
    JPEG_ICC_PREFIX,
    JPEG_MARKER,
    JPEG_SEGMENT_LENGTH,
    JPEG_SOI,
    JPEG_START_OF_SCAN,
    PNG_CHUNK_OVERHEAD,
    PNG_COLOR_CHUNKS,
    PNG_ICC_CHUNK,
    PNG_ICC_DEFLATE,
    PNG_ICC_NAME,
    PNG_IMAGE_DATA,
    PNG_SIGNATURE,
)

__all__ = ["embed_profile", "embedded_profile"]


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
    >>> from svgwriter._internal._color._icc_embedded import embedded_profile
    >>> embedded_profile(b"plain bytes") is None
    True
    """
    if data.startswith(PNG_SIGNATURE):
        return _png_profile(data)
    if data.startswith(JPEG_SOI):
        return _jpeg_profile(data)
    return None


def _png_chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def _embed_png(data: bytes, profile: bytes) -> bytes:
    header_end = len(PNG_SIGNATURE) + PNG_CHUNK_OVERHEAD + struct.unpack_from(">I", data, len(PNG_SIGNATURE))[0]
    parts = [data[:header_end], _png_chunk(PNG_ICC_CHUNK, PNG_ICC_NAME + PNG_ICC_DEFLATE + zlib.compress(profile))]
    position = header_end
    while position + PNG_CHUNK_OVERHEAD <= len(data):
        (length,) = struct.unpack_from(">I", data, position)
        end = position + length + PNG_CHUNK_OVERHEAD
        if data[position + 4:position + 8] not in PNG_COLOR_CHUNKS:
            parts.append(data[position:end])
        position = end
    return b"".join(parts)


def _embed_jpeg(data: bytes, profile: bytes) -> bytes:
    position = len(JPEG_SOI)
    if data[position + 1] == JPEG_APP0:
        position += 2 + struct.unpack_from(">H", data, position + 2)[0]
    pieces = [profile[i:i + JPEG_ICC_CHUNK] for i in range(0, len(profile), JPEG_ICC_CHUNK)]
    segments = [bytes([JPEG_MARKER, JPEG_APP2]) + struct.pack(">H", JPEG_SEGMENT_LENGTH + JPEG_ICC_HEADER + len(piece))
                + JPEG_ICC_PREFIX + bytes([index, len(pieces)]) + piece for index, piece in enumerate(pieces, 1)]
    return data[:position] + b"".join(segments) + data[position:]


def embed_profile(data: bytes, profile: bytes) -> bytes:
    """Embed an ICC profile in PNG (``iCCP``) or JPEG (``APP2``) file contents.

    Parameters
    ----------
    data : bytes
        An encoded PNG (or APNG) or JPEG.
    profile : bytes
        The ICC profile; a PNG's ``sRGB``, ``gAMA``, ``cHRM`` or older ``iCCP`` chunks are replaced.

    Returns
    -------
    bytes
        The file with the profile; JPEG profiles above 64 KB span several ``APP2`` segments.

    Raises
    ------
    ValueError
        If `data` is neither PNG nor JPEG.

    See Also
    --------
    embedded_profile : Read the profile back.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.ops import encode
    >>> from svgwriter._internal._color._icc_embedded import embed_profile, embedded_profile
    >>> png = encode(np.ones((1, 1, 4)))
    >>> embedded_profile(embed_profile(png, b"profile bytes"))
    b'profile bytes'
    """
    if data.startswith(PNG_SIGNATURE):
        return _embed_png(data, profile)
    if data.startswith(JPEG_SOI):
        return _embed_jpeg(data, profile)
    raise ValueError("only PNG and JPEG files can carry an embedded ICC profile here")
