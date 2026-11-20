"""
The pure-Python GIF encoder: median-cut palettes, LZW and animated GIFs.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence

import numpy as np

from ._constants import (
    GIF_APPLICATION,
    GIF_APPLICATION_SIZE,
    GIF_BLOCK_SIZE,
    GIF_CENTISECONDS,
    GIF_DISPOSE_BACKGROUND,
    GIF_EXTENSION,
    GIF_FLAG_TRANSPARENT,
    GIF_GRAPHIC_CONTROL,
    GIF_GRAPHIC_CONTROL_SIZE,
    GIF_HEADER,
    GIF_IMAGE_SEPARATOR,
    GIF_LOOP_BLOCK_SIZE,
    GIF_MAX_CODE_SIZE,
    GIF_MAX_CODES,
    GIF_MAX_COLORS,
    GIF_MAX_DIMENSION,
    GIF_MIN_CODE_SIZE,
    GIF_MIN_PALETTE,
    GIF_NETSCAPE,
    GIF_OPAQUE_THRESHOLD,
    GIF_PALETTE_FLAG,
    GIF_TRAILER,
)
from ._rgba import _check_rgba

__all__ = ["encode_gif", "encode_gif_animation"]


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
    _check_gif_size(rows, columns)
    table, bits, frame = _gif_frame(pixels, delay=0, local=False)
    screen = struct.pack("<HHBBB", columns, rows, GIF_PALETTE_FLAG | ((bits - 1) << 4) | (bits - 1), 0, 0)
    return GIF_HEADER + screen + table + frame + GIF_TRAILER


def _check_gif_size(rows: int, columns: int) -> None:
    if not 0 < rows <= GIF_MAX_DIMENSION or not 0 < columns <= GIF_MAX_DIMENSION:
        raise ValueError(f"GIF dimensions must be 1..{GIF_MAX_DIMENSION}, got {columns}x{rows}")


def _gif_frame(pixels: np.ndarray, *, delay: int, local: bool) -> tuple[bytes, int, bytes]:
    """Quantize one frame: its color table, table bits and the extension + image blocks."""
    rows, columns = pixels.shape[:2]
    indices, palette, transparent = _quantize(pixels)
    bits = max(int(np.ceil(np.log2(max(len(palette), GIF_MIN_PALETTE)))), 1)
    table = np.zeros((1 << bits, 3), np.uint8)
    table[: len(palette)] = palette
    min_code_size = max(bits, GIF_MIN_CODE_SIZE)
    control = b""
    if transparent is not None or delay:
        flags = (GIF_FLAG_TRANSPARENT if transparent is not None else 0) | (GIF_DISPOSE_BACKGROUND if local else 0)
        control = struct.pack("<BBBBHBB", GIF_EXTENSION, GIF_GRAPHIC_CONTROL, GIF_GRAPHIC_CONTROL_SIZE,
                              flags, delay, transparent or 0, 0)
    packed = (GIF_PALETTE_FLAG | (bits - 1)) if local else 0
    descriptor = struct.pack("<BHHHHB", GIF_IMAGE_SEPARATOR, 0, 0, columns, rows, packed)
    compressed = _lzw(indices.tobytes(), min_code_size)
    blocks = b"".join(
        bytes([len(chunk)]) + chunk
        for chunk in (compressed[i:i + GIF_BLOCK_SIZE] for i in range(0, len(compressed), GIF_BLOCK_SIZE))
    )
    image = descriptor + (table.tobytes() if local else b"") + bytes([min_code_size]) + blocks + b"\x00"
    return table.tobytes(), bits, control + image


def encode_gif_animation(frames: Sequence[np.ndarray], fps: float, *, loop: int = 0) -> bytes:
    """Encode RGBA frames as an animated GIF89a, each frame with its own palette.

    Parameters
    ----------
    frames : sequence of numpy.ndarray
        ``(H, W, 4)`` ``uint8`` frames of equal size.
    fps : float
        Frames per second; GIF stores delays in hundredths of a second.
    loop : int, optional
        Number of repeats; 0 loops forever. Defaults to 0.

    Returns
    -------
    bytes
        The GIF file.

    Raises
    ------
    ValueError
        If there are no frames or their sizes differ.

    Examples
    --------
    >>> import numpy as np
    >>> frames = [np.full((2, 2, 4), v, np.uint8) for v in (0, 255)]
    >>> encode_gif_animation(frames, fps=10)[:6]
    b'GIF89a'
    """
    if not len(frames):
        raise ValueError("an animated GIF needs at least one frame")
    first = _check_rgba(frames[0])
    rows, columns = first.shape[:2]
    _check_gif_size(rows, columns)
    delay = max(round(GIF_CENTISECONDS / fps), 1)
    screen = struct.pack("<HHBBB", columns, rows, 0, 0, 0)
    looping = (bytes([GIF_EXTENSION, GIF_APPLICATION, GIF_APPLICATION_SIZE]) + GIF_NETSCAPE
               + struct.pack("<BBHB", GIF_LOOP_BLOCK_SIZE, 1, loop, 0))
    parts = [GIF_HEADER, screen, looping]
    for frame in frames:
        pixels = _check_rgba(frame)
        if pixels.shape[:2] != (rows, columns):
            raise ValueError(f"frame size {pixels.shape[1]}x{pixels.shape[0]} differs from {columns}x{rows}")
        parts.append(_gif_frame(pixels, delay=delay, local=True)[2])
    return b"".join(parts) + GIF_TRAILER
