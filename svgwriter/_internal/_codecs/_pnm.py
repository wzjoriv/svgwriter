"""
The pure-Python Netpbm (PBM, PGM, PPM) encoder and decoder.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import numpy as np

from .._constants import (
    CHANNEL_MAX,
)
from ._codec_constants import (
    LUMA,
    PNM_BINARY_FROM,
    PNM_BITMAP,
    PNM_COMMENT,
    PNM_MAGIC,
    PNM_WHITESPACE,
    UINT16_MAX,
    WHITE,
)
from ._rgba import _check_rgba, _composite

__all__ = ["decode_pnm", "encode_pnm", "is_pnm"]


def encode_pnm(rgba: np.ndarray, *, gray: bool | None = None, background: Sequence[int] = WHITE) -> bytes:
    """Encode a uint8 RGBA array as binary PPM (P6) or PGM (P5), compositing alpha first.

    Parameters
    ----------
    rgba : numpy.ndarray
        Straight ``uint8`` array of shape ``(H, W, 4)``.
    gray : bool, optional
        True writes PGM, False writes PPM, None picks PGM only when every
        pixel is gray. Defaults to None.
    background : sequence of int, optional
        Opaque ``(r, g, b)`` color, 0 to 255, that transparency is flattened
        onto, since PNM has no alpha. Defaults to white.

    Returns
    -------
    bytes
        The P6 or P5 file with ``maxval`` 255.

    Raises
    ------
    ValueError
        If `rgba` is not a ``uint8`` ``(H, W, 4)`` array.

    See Also
    --------
    decode_pnm : Read PNM files back.
    encode_bmp : Keeps alpha.

    Notes
    -----
    Forcing ``gray=True`` converts with Rec. 601 luma weights.

    Examples
    --------
    >>> import numpy as np
    >>> encode_pnm(np.zeros((1, 2, 4), np.uint8))[:11]
    b'P5\\n2 1\\n255\\n'
    >>> encode_pnm(np.full((1, 2, 4), 255, np.uint8), gray=False)[:2]
    b'P6'
    """
    rows, columns = _check_rgba(rgba).shape[:2]
    color = _composite(rgba, background)
    if gray is None:
        gray = bool(np.all(color[..., 0] == color[..., 1]) and np.all(color[..., 1] == color[..., 2]))
    if gray:
        luma = color[..., 0] if np.all(color == color[..., :1]) else np.rint(color @ LUMA)
        body = np.clip(luma, 0, CHANNEL_MAX).astype(np.uint8)
    else:
        body = color
    magic = b"P5" if gray else b"P6"
    return b"%s\n%d %d\n%d\n" % (magic, columns, rows, CHANNEL_MAX) + body.tobytes()


def is_pnm(data: bytes) -> bool:
    """Whether the bytes start with a PNM magic number, ``P1`` to ``P6``."""
    return PNM_MAGIC.fullmatch(data[:2]) is not None


def _token(data: bytes, position: int) -> tuple[bytes, int]:
    """Next whitespace-delimited header token after skipping comments."""
    length = len(data)
    while position < length:
        if data[position] in PNM_WHITESPACE:
            position += 1
        elif data[position] == ord("#"):
            while position < length and data[position] not in b"\r\n":
                position += 1
        else:
            break
    start = position
    while position < length and data[position] not in PNM_WHITESPACE and data[position] != ord("#"):
        position += 1
    if start == position:
        raise ValueError("truncated PNM header")
    return data[start:position], position


def decode_pnm(data: bytes) -> np.ndarray:
    """Decode a PBM, PGM or PPM file (P1 to P6, ASCII or binary) into an array.

    Parameters
    ----------
    data : bytes
        The file contents; ``maxval`` may be up to 65535.

    Returns
    -------
    numpy.ndarray
        ``(H, W)`` for bitmaps and graymaps, ``(H, W, 3)`` for pixmaps.
        ``uint8`` when ``maxval`` is 255 (bitmaps map 1 to black), otherwise
        ``float32`` in ``0..1``. Accepted by ``Pixels.from_array``.

    Raises
    ------
    ValueError
        If the magic number, header or sample count is invalid.

    See Also
    --------
    encode_pnm : Write PPM and PGM.

    Notes
    -----
    Only the first image of a multi-image file is read.

    Examples
    --------
    >>> decode_pnm(b"P2\\n2 1\\n255\\n0 255\\n").tolist()
    [[0, 255]]
    >>> decode_pnm(b"P1 2 1 10").tolist()
    [[0, 255]]
    """
    if not is_pnm(data):
        raise ValueError("not a PNM file: bad magic number")
    kind = data[1] - ord("0")
    position = 2
    width_token, position = _token(data, position)
    height_token, position = _token(data, position)
    try:
        width, height = int(width_token), int(height_token)
    except ValueError:
        raise ValueError("invalid PNM dimensions") from None
    if width <= 0 or height <= 0:
        raise ValueError("invalid PNM dimensions")
    maxval = 1
    if kind not in PNM_BITMAP:
        maxval_token, position = _token(data, position)
        try:
            maxval = int(maxval_token)
        except ValueError:
            raise ValueError("invalid PNM maxval") from None
        if not 0 < maxval <= UINT16_MAX:
            raise ValueError(f"PNM maxval must be 1..{UINT16_MAX}, got {maxval}")
    channels = 3 if kind in (3, 6) else 1
    count = width * height * channels
    body = data[position:]
    if kind == 1:
        digits = re.sub(rb"[^01]", b"", PNM_COMMENT.sub(b"", body))
        samples = np.frombuffer(digits, np.uint8)[:count] - ord("0")
    elif kind == 4:
        stride = (width + 7) // 8
        packed = np.frombuffer(body[1:], np.uint8)[: stride * height]
        if packed.size < stride * height:
            raise ValueError("truncated PNM data")
        samples = np.unpackbits(packed.reshape(height, stride), axis=1)[:, :width].reshape(-1)
    elif kind < PNM_BINARY_FROM:
        tokens = PNM_COMMENT.sub(b"", body).split()
        try:
            samples = np.array(tokens[:count], dtype=np.int64)
        except ValueError:
            raise ValueError("invalid PNM sample") from None
    else:
        dtype = np.dtype(">u2") if maxval > CHANNEL_MAX else np.dtype(np.uint8)
        samples = np.frombuffer(body[1:], dtype)[:count]
    if samples.size < count:
        raise ValueError("truncated PNM data")
    if kind in PNM_BITMAP:
        result = ((1 - samples.astype(np.int64)) * CHANNEL_MAX).astype(np.uint8)
    elif maxval == CHANNEL_MAX:
        result = samples.astype(np.uint8)
    else:
        if samples.max(initial=0) > maxval:
            raise ValueError("PNM sample exceeds maxval")
        result = samples.astype(np.float32) / np.float32(maxval)
    return result.reshape(height, width) if channels == 1 else result.reshape(height, width, 3)
