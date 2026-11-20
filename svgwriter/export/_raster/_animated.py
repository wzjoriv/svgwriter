"""
Animated PNG (APNG) and animated WebP, assembled from frames that skia encodes one at a time.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Sequence

import numpy as np

from ._constants import (
    APNG_DELAY_DENOMINATOR,
    BLEND_SOURCE,
    CHUNK_HEADER,
    CRC_SIZE,
    DISPOSE_NONE,
    LOSSLESS,
    MILLISECONDS,
    PNG_SIGNATURE,
    RIFF_HEADER,
    WEBP_ALPHA_FLAG,
    WEBP_ANIMATION_FLAG,
    WEBP_CHUNK_HEADER,
    WEBP_NO_BLEND,
)

__all__ = ["encode_apng", "encode_webp_animation"]


def _encode_png(frame: np.ndarray) -> bytes:
    from ...elements.structure import Pixels

    return Pixels.from_array(frame).encode("png")


def _chunks(png: bytes) -> list[tuple[bytes, bytes]]:
    """The ``(type, data)`` chunks of a PNG file."""
    chunks, position = [], len(PNG_SIGNATURE)
    while position < len(png):
        length, kind = struct.unpack(">I4s", png[position:position + CHUNK_HEADER])
        chunks.append((kind, png[position + CHUNK_HEADER:position + CHUNK_HEADER + length]))
        position += CHUNK_HEADER + length + CRC_SIZE
    return chunks


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_apng(frames: Sequence[np.ndarray], fps: float, *, loop: int = 0) -> bytes:
    """Animated PNG from RGBA frames (full color and alpha, lossless).

    Parameters
    ----------
    frames : sequence of numpy.ndarray
        ``(H, W, 4)`` ``uint8`` frames of one size.
    fps : float
        Frames per second.
    loop : int, optional
        Repeats; 0 loops forever. Defaults to 0.

    Returns
    -------
    bytes
        The ``.png`` file; viewers without APNG support show the first frame.

    Raises
    ------
    ValueError
        If there are no frames or their sizes differ.

    Examples
    --------
    >>> import numpy as np
    >>> data = encode_apng([np.zeros((2, 2, 4), np.uint8), np.full((2, 2, 4), 255, np.uint8)], fps=10)
    >>> data[:8] == PNG_SIGNATURE, b"acTL" in data
    (True, True)
    """
    if not len(frames):
        raise ValueError("an animation needs at least one frame")
    rows, columns = frames[0].shape[:2]
    delay = max(round(APNG_DELAY_DENOMINATOR / fps), 1)
    out = [PNG_SIGNATURE]
    sequence = 0
    for index, frame in enumerate(frames):
        if frame.shape[:2] != (rows, columns):
            raise ValueError(f"frame {index} is {frame.shape[1]}x{frame.shape[0]}, not {columns}x{rows}")
        chunks = _chunks(_encode_png(frame))
        if index == 0:
            out.append(_chunk(b"IHDR", next(data for kind, data in chunks if kind == b"IHDR")))
            out.append(_chunk(b"acTL", struct.pack(">II", len(frames), loop)))
        control = struct.pack(">IIIIIHHBB", sequence, columns, rows, 0, 0, delay, APNG_DELAY_DENOMINATOR,
                              DISPOSE_NONE, BLEND_SOURCE)
        out.append(_chunk(b"fcTL", control))
        sequence += 1
        for kind, data in chunks:
            if kind != b"IDAT":
                continue
            if index == 0:
                out.append(_chunk(b"IDAT", data))
            else:
                out.append(_chunk(b"fdAT", struct.pack(">I", sequence) + data))
                sequence += 1
    out.append(_chunk(b"IEND", b""))
    return b"".join(out)


def _riff_chunks(webp: bytes) -> list[tuple[bytes, bytes]]:
    chunks, position = [], RIFF_HEADER
    while position < len(webp):
        kind, size = struct.unpack("<4sI", webp[position:position + WEBP_CHUNK_HEADER])
        chunks.append((kind, webp[position + WEBP_CHUNK_HEADER:position + WEBP_CHUNK_HEADER + size]))
        position += WEBP_CHUNK_HEADER + size + (size & 1)
    return chunks


def _webp_chunk(kind: bytes, data: bytes) -> bytes:
    return kind + struct.pack("<I", len(data)) + data + (b"\x00" if len(data) & 1 else b"")


def _uint24(value: int) -> bytes:
    return struct.pack("<I", value)[:3]


def encode_webp_animation(frames: Sequence[np.ndarray], fps: float, *, loop: int = 0) -> bytes:
    """Animated WebP from RGBA frames (each frame lossless).

    Parameters
    ----------
    frames : sequence of numpy.ndarray
        ``(H, W, 4)`` ``uint8`` frames of one size.
    fps : float
        Frames per second.
    loop : int, optional
        Repeats; 0 loops forever. Defaults to 0.

    Returns
    -------
    bytes
        The ``.webp`` file.

    Raises
    ------
    ValueError
        If there are no frames or their sizes differ.

    Examples
    --------
    >>> import numpy as np
    >>> data = encode_webp_animation([np.zeros((2, 2, 4), np.uint8)] * 2, fps=10)
    >>> data[:4], data[8:12], b"ANIM" in data
    (b'RIFF', b'WEBP', True)
    """
    from ...elements.structure import Pixels

    if not len(frames):
        raise ValueError("an animation needs at least one frame")
    rows, columns = frames[0].shape[:2]
    duration = max(round(MILLISECONDS / fps), 1)
    header = _webp_chunk(b"VP8X", bytes([WEBP_ANIMATION_FLAG | WEBP_ALPHA_FLAG, 0, 0, 0])
                         + _uint24(columns - 1) + _uint24(rows - 1))
    body = [header, _webp_chunk(b"ANIM", struct.pack("<IH", 0, loop))]
    for index, frame in enumerate(frames):
        if frame.shape[:2] != (rows, columns):
            raise ValueError(f"frame {index} is {frame.shape[1]}x{frame.shape[0]}, not {columns}x{rows}")
        encoded = Pixels.from_array(frame).encode("webp", quality=LOSSLESS)
        payload = b"".join(_webp_chunk(kind, data) for kind, data in _riff_chunks(encoded)
                           if kind in (b"ALPH", b"VP8 ", b"VP8L"))
        placement = (_uint24(0) + _uint24(0) + _uint24(columns - 1) + _uint24(rows - 1) + _uint24(duration)
                     + bytes([WEBP_NO_BLEND]))
        body.append(_webp_chunk(b"ANMF", placement + payload))
    content = b"WEBP" + b"".join(body)
    return b"RIFF" + struct.pack("<I", len(content)) + content
