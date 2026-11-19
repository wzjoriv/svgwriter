"""
Pure-numpy BMP, GIF and PNM encoders, and a PNM decoder.
"""

from __future__ import annotations

import re
import struct
from collections.abc import Callable, Sequence
from typing import Final

import numpy as np

__all__ = ["ENCODERS", "decode_pnm", "encode_bmp", "encode_gif", "encode_pnm", "is_pnm", "to_uint8"]

CHANNEL_MAX: Final = 255
UINT16_MAX: Final = 65535
RGBA_CHANNELS: Final = 4
WHITE: Final = (255, 255, 255)
LUMA: Final = np.array([0.299, 0.587, 0.114], np.float64)

BMP_MAGIC: Final = b"BM"
BMP_FILE_HEADER_SIZE: Final = 14
BMP_V4_HEADER_SIZE: Final = 108
BMP_BITS_PER_PIXEL: Final = 32
BMP_BI_BITFIELDS: Final = 3
BMP_PIXELS_PER_METER: Final = 2835
BMP_LCS_SRGB: Final = 0x73524742
BMP_MASKS: Final = (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)

GIF_HEADER: Final = b"GIF89a"
GIF_TRAILER: Final = b"\x3b"
GIF_EXTENSION: Final = 0x21
GIF_GRAPHIC_CONTROL: Final = 0xF9
GIF_GRAPHIC_CONTROL_SIZE: Final = 4
GIF_FLAG_TRANSPARENT: Final = 0x01
GIF_IMAGE_SEPARATOR: Final = 0x2C
GIF_PALETTE_FLAG: Final = 0x80
GIF_MAX_COLORS: Final = 256
GIF_MIN_PALETTE: Final = 2
GIF_MAX_DIMENSION: Final = UINT16_MAX
GIF_MIN_CODE_SIZE: Final = 2
GIF_MAX_CODE_SIZE: Final = 12
GIF_MAX_CODES: Final = 1 << GIF_MAX_CODE_SIZE
GIF_BLOCK_SIZE: Final = 255
GIF_OPAQUE_THRESHOLD: Final = 128

PNM_MAGIC: Final = re.compile(rb"P[1-6]")
PNM_WHITESPACE: Final = b" \t\r\n\v\f"
PNM_BITMAP: Final = (1, 4)
PNM_BINARY_FROM: Final = 4
_PNM_COMMENT: Final = re.compile(rb"#[^\r\n]*")


def to_uint8(array: object) -> np.ndarray:
    """Convert floats in ``0..1`` or uint8 to a C-contiguous uint8 array.

    Parameters
    ----------
    array : array-like
        Pixel values; floats are scaled from ``0..1`` and rounded.

    Returns
    -------
    numpy.ndarray
        The ``uint8`` array, unchanged if it already was one.

    Examples
    --------
    >>> to_uint8([0.0, 0.5, 1.0]).tolist()
    [0, 128, 255]
    """
    data = np.asarray(array)
    if data.dtype != np.uint8:
        data = np.clip(np.rint(data * CHANNEL_MAX), 0, CHANNEL_MAX).astype(np.uint8)
    return np.ascontiguousarray(data)


def _check_rgba(rgba: object) -> np.ndarray:
    """Validate and return a uint8 ``(H, W, 4)`` array."""
    data = np.asarray(rgba)
    if data.dtype != np.uint8 or data.ndim != 3 or data.shape[2] != RGBA_CHANNELS:
        raise ValueError(f"expected a uint8 (H, W, 4) array, got {data.dtype} {data.shape}")
    return data


def _composite(rgba: np.ndarray, background: Sequence[int]) -> np.ndarray:
    """Flatten straight RGBA onto an opaque background, returning uint8 ``(H, W, 3)``."""
    alpha = rgba[..., 3:].astype(np.float64) / CHANNEL_MAX
    under = np.asarray(background, np.float64).reshape(1, 1, 3)
    mixed = rgba[..., :3] * alpha + under * (1.0 - alpha)
    return np.clip(np.rint(mixed), 0, CHANNEL_MAX).astype(np.uint8)


def encode_bmp(rgba: np.ndarray) -> bytes:
    """Encode a uint8 RGBA array as a 32-bit BMP with a BITMAPV4 header, keeping alpha.

    Parameters
    ----------
    rgba : numpy.ndarray
        Straight ``uint8`` array of shape ``(H, W, 4)``.

    Returns
    -------
    bytes
        The BMP file, with rows stored bottom-up as BGRA.

    Raises
    ------
    ValueError
        If `rgba` is not a ``uint8`` ``(H, W, 4)`` array.

    See Also
    --------
    encode_gif : One-frame GIF.
    encode_pnm : PPM and PGM.

    Notes
    -----
    The header declares ``BI_BITFIELDS`` with explicit channel masks and an
    sRGB color space, so readers that honor the alpha mask keep transparency.

    Examples
    --------
    >>> import numpy as np
    >>> data = encode_bmp(np.zeros((2, 3, 4), np.uint8))
    >>> data[:2], len(data)
    (b'BM', 146)
    """
    pixels = _check_rgba(rgba)
    rows, columns = pixels.shape[:2]
    body = np.ascontiguousarray(pixels[::-1][..., [2, 1, 0, 3]]).tobytes()
    offset = BMP_FILE_HEADER_SIZE + BMP_V4_HEADER_SIZE
    file_header = struct.pack("<2sIHHI", BMP_MAGIC, offset + len(body), 0, 0, offset)
    info = struct.pack(
        "<IiiHHIIiiII4I", BMP_V4_HEADER_SIZE, columns, rows, 1, BMP_BITS_PER_PIXEL, BMP_BI_BITFIELDS, len(body),
        BMP_PIXELS_PER_METER, BMP_PIXELS_PER_METER, 0, 0, *BMP_MASKS,
    )
    colorspace = struct.pack("<I36xIII", BMP_LCS_SRGB, 0, 0, 0)
    return file_header + info + colorspace + body


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


def _median_cut(colors: np.ndarray, counts: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray]:
    """Split unique colors into at most ``limit`` boxes; return the palette and each color's box."""
    boxes = [np.arange(len(colors))]
    while len(boxes) < limit:
        splittable = [i for i, box in enumerate(boxes) if len(box) > 1]
        if not splittable:
            break
        pick = max(splittable, key=lambda i: (counts[boxes[i]].sum(), -i))
        box = boxes.pop(pick)
        span = colors[box].max(axis=0).astype(np.int32) - colors[box].min(axis=0)
        channel = int(np.argmax(span))
        order = box[np.argsort(colors[box, channel], kind="stable")]
        cumulative = np.cumsum(counts[order])
        cut = int(np.searchsorted(cumulative, cumulative[-1] / 2.0)) + 1
        cut = min(max(cut, 1), len(order) - 1)
        boxes.insert(pick, order[:cut])
        boxes.insert(pick + 1, order[cut:])
    palette = np.empty((len(boxes), 3), np.uint8)
    membership = np.empty(len(colors), np.int64)
    for index, box in enumerate(boxes):
        weights = counts[box].astype(np.float64)
        palette[index] = np.rint((colors[box] * weights[:, None]).sum(axis=0) / weights.sum())
        membership[box] = index
    return palette, membership


def _quantize(rgba: np.ndarray) -> tuple[np.ndarray, np.ndarray, int | None]:
    """Reduce to indices, a palette and the transparent index (None when fully opaque)."""
    rows, columns = rgba.shape[:2]
    opaque = (rgba[..., 3] >= GIF_OPAQUE_THRESHOLD).reshape(-1)
    transparent = not opaque.all()
    limit = GIF_MAX_COLORS - int(transparent)
    flat = rgba[..., :3].reshape(-1, 3)[opaque]
    indices = np.zeros(rows * columns, np.uint8)
    palette = np.zeros((0, 3), np.uint8)
    if len(flat):
        packed = (flat[:, 0].astype(np.uint32) << 16) | (flat[:, 1].astype(np.uint32) << 8) | flat[:, 2]
        unique, inverse, counts = np.unique(packed, return_inverse=True, return_counts=True)
        colors = np.stack([(unique >> 16) & 0xFF, (unique >> 8) & 0xFF, unique & 0xFF], axis=1).astype(np.uint8)
        if len(unique) <= limit:
            palette, membership = colors, np.arange(len(unique))
        else:
            palette, membership = _median_cut(colors, counts, limit)
        indices[opaque] = membership[inverse.reshape(-1)]
    transparent_index = None
    if transparent:
        transparent_index = len(palette)
        palette = np.vstack([palette, np.zeros((1, 3), np.uint8)])
        indices[~opaque] = transparent_index
    return indices.reshape(rows, columns), palette, transparent_index


def _lzw(indices: bytes, min_code_size: int) -> bytes:
    """GIF variable-length LZW with clear codes when the 12-bit table fills."""
    clear = 1 << min_code_size
    end = clear + 1
    out = bytearray()
    state = [0, 0]

    def emit(code: int, size: int) -> None:
        bits = state[0] | (code << state[1])
        count = state[1] + size
        while count >= 8:
            out.append(bits & 0xFF)
            bits >>= 8
            count -= 8
        state[0], state[1] = bits, count

    table: dict[int, int] = {}
    size = min_code_size + 1
    next_code = end + 1
    emit(clear, size)
    prefix = indices[0]
    for byte in indices[1:]:
        key = (prefix << 8) | byte
        found = table.get(key)
        if found is not None:
            prefix = found
            continue
        emit(prefix, size)
        if next_code < GIF_MAX_CODES:
            table[key] = next_code
            if next_code == (1 << size) and size < GIF_MAX_CODE_SIZE:
                size += 1
            next_code += 1
        else:
            emit(clear, size)
            table.clear()
            size = min_code_size + 1
            next_code = end + 1
        prefix = byte
    emit(prefix, size)
    emit(end, size)
    if state[1]:
        out.append(state[0] & 0xFF)
    return bytes(out)


def encode_gif(rgba: np.ndarray) -> bytes:
    """Encode a uint8 RGBA array as a one-frame GIF89a with at most 256 colors.

    Parameters
    ----------
    rgba : numpy.ndarray
        Straight ``uint8`` array of shape ``(H, W, 4)``, at most 65535 pixels per side.

    Returns
    -------
    bytes
        The GIF file.

    Raises
    ------
    ValueError
        If `rgba` is not a ``uint8`` ``(H, W, 4)`` array, is empty, or is too large.

    See Also
    --------
    encode_bmp : Full 32-bit color with alpha.

    Notes
    -----
    Colors are reduced by a deterministic median cut weighted by pixel count;
    images with at most 256 distinct colors keep them exactly. Pixels with
    alpha below 0.5 share one transparent palette index, declared in a
    Graphic Control Extension.

    Examples
    --------
    >>> import numpy as np
    >>> data = encode_gif(np.full((2, 2, 4), 255, np.uint8))
    >>> data[:6], data[-1:]
    (b'GIF89a', b';')
    """
    pixels = _check_rgba(rgba)
    rows, columns = pixels.shape[:2]
    if not 0 < rows <= GIF_MAX_DIMENSION or not 0 < columns <= GIF_MAX_DIMENSION:
        raise ValueError(f"GIF dimensions must be 1..{GIF_MAX_DIMENSION}, got {columns}x{rows}")
    indices, palette, transparent = _quantize(pixels)
    bits = max(int(np.ceil(np.log2(max(len(palette), GIF_MIN_PALETTE)))), 1)
    table = np.zeros((1 << bits, 3), np.uint8)
    table[: len(palette)] = palette
    min_code_size = max(bits, GIF_MIN_CODE_SIZE)
    screen = struct.pack("<HHBBB", columns, rows, GIF_PALETTE_FLAG | ((bits - 1) << 4) | (bits - 1), 0, 0)
    control = b""
    if transparent is not None:
        control = struct.pack("<BBBBHBB", GIF_EXTENSION, GIF_GRAPHIC_CONTROL, GIF_GRAPHIC_CONTROL_SIZE,
                              GIF_FLAG_TRANSPARENT, 0, transparent, 0)
    descriptor = struct.pack("<BHHHHB", GIF_IMAGE_SEPARATOR, 0, 0, columns, rows, 0)
    compressed = _lzw(indices.tobytes(), min_code_size)
    blocks = b"".join(
        bytes([len(chunk)]) + chunk
        for chunk in (compressed[i:i + GIF_BLOCK_SIZE] for i in range(0, len(compressed), GIF_BLOCK_SIZE))
    )
    return (GIF_HEADER + screen + table.tobytes() + control + descriptor + bytes([min_code_size]) + blocks
            + b"\x00" + GIF_TRAILER)


ENCODERS: Final[dict[str, Callable[[np.ndarray], bytes]]] = {
    "bmp": encode_bmp,
    "gif": encode_gif,
    "ppm": encode_pnm,
}


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
        digits = re.sub(rb"[^01]", b"", _PNM_COMMENT.sub(b"", body))
        samples = np.frombuffer(digits, np.uint8)[:count] - ord("0")
    elif kind == 4:
        stride = (width + 7) // 8
        packed = np.frombuffer(body[1:], np.uint8)[: stride * height]
        if packed.size < stride * height:
            raise ValueError("truncated PNM data")
        samples = np.unpackbits(packed.reshape(height, stride), axis=1)[:, :width].reshape(-1)
    elif kind < PNM_BINARY_FROM:
        tokens = _PNM_COMMENT.sub(b"", body).split()
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
