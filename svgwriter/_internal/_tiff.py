"""
A pure-numpy baseline TIFF encoder: RGB, RGBA or CMYK, deflate-compressed, with an optional ICC profile.
"""

from __future__ import annotations

import struct
import zlib

import numpy as np

from ._codec_constants import (
    TIFF_ALPHA_UNASSOCIATED,
    TIFF_COMPRESSION_DEFLATE,
    TIFF_ENTRY,
    TIFF_HEADER,
    TIFF_INK_CMYK,
    TIFF_INLINE,
    TIFF_PHOTOMETRIC,
    TIFF_PLANAR_CHUNKY,
    TIFF_RESOLUTION_DENOMINATOR,
    TIFF_TAGS,
    TIFF_TYPES,
    TIFF_UNIT_INCH,
)

__all__ = ["encode_tiff"]

BITS_PER_SAMPLE = 8


def _value(kind: str, values: list[int] | bytes) -> bytes:
    code_format = TIFF_TYPES[kind][1]
    return values if isinstance(values, bytes) else struct.pack(f"<{len(values)}{code_format}", *values)


def encode_tiff(pixels: np.ndarray, space: str = "RGB", *, dpi: float, profile: bytes | None = None) -> bytes:
    """Encode ``uint8`` pixels as a single-strip, deflate-compressed little-endian TIFF.

    Parameters
    ----------
    pixels : numpy.ndarray
        ``(H, W, 3)`` RGB, ``(H, W, 4)`` RGBA with straight alpha, or ``(H, W, 4)`` CMYK ink
        (255 is full ink).
    space : {"RGB", "CMYK"}, optional
        How to read the channels. Defaults to ``"RGB"``.
    dpi : float
        Pixels per inch written as the resolution.
    profile : bytes, optional
        An ICC profile to embed (tag 34675). Defaults to None.

    Returns
    -------
    bytes
        The TIFF file.

    Raises
    ------
    ValueError
        For an unknown space or a channel count it cannot hold.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter._internal._tiff import encode_tiff
    >>> encode_tiff(np.zeros((2, 3, 4), np.uint8), dpi=96)[:4]
    b'II*\\x00'
    """
    if space not in TIFF_PHOTOMETRIC:
        raise ValueError(f"TIFF pixels must be RGB or CMYK, got {space!r}")
    rows, columns, samples = pixels.shape
    alpha = space == "RGB" and samples == len(space) + 1
    if samples != len(space) + alpha:
        raise ValueError(f"{space} TIFF pixels need {len(space)} channels{' or 4' if space == 'RGB' else ''}, got {samples}")
    strip = zlib.compress(np.ascontiguousarray(pixels, dtype=np.uint8).tobytes())
    resolution = [round(dpi * TIFF_RESOLUTION_DENOMINATOR), TIFF_RESOLUTION_DENOMINATOR]
    fields: list[tuple[str, str, list[int] | bytes]] = [
        ("width", "long", [columns]), ("height", "long", [rows]), ("bits", "short", [BITS_PER_SAMPLE] * samples),
        ("compression", "short", [TIFF_COMPRESSION_DEFLATE]), ("photometric", "short", [TIFF_PHOTOMETRIC[space]]),
        ("strip_offsets", "long", [0]), ("samples", "short", [samples]), ("rows_per_strip", "long", [rows]),
        ("strip_bytes", "long", [len(strip)]), ("x_resolution", "rational", resolution),
        ("y_resolution", "rational", resolution), ("planar", "short", [TIFF_PLANAR_CHUNKY]),
        ("resolution_unit", "short", [TIFF_UNIT_INCH]),
    ]
    if space == "CMYK":
        fields.append(("ink_set", "short", [TIFF_INK_CMYK]))
    if alpha:
        fields.append(("extra_samples", "short", [TIFF_ALPHA_UNASSOCIATED]))
    if profile:
        fields.append(("icc", "undefined", profile))
    fields.sort(key=lambda field: TIFF_TAGS[field[0]])
    first_ifd = len(TIFF_HEADER) + TIFF_INLINE
    extra_start = first_ifd + 2 + TIFF_ENTRY * len(fields) + TIFF_INLINE
    long_values = [_value(kind, values) for _, kind, values in fields]
    strip_offset = extra_start + sum(len(d) + len(d) % 2 for d in long_values if len(d) > TIFF_INLINE)
    entries, extra = [], b""
    for name, kind, values in fields:
        data = _value(kind, [strip_offset] if name == "strip_offsets" else values)
        count = len(data) // struct.calcsize(TIFF_TYPES[kind][1]) // (2 if kind == "rational" else 1)
        head = struct.pack("<HHI", TIFF_TAGS[name], TIFF_TYPES[kind][0], count)
        if len(data) > TIFF_INLINE:
            entries.append(head + struct.pack("<I", extra_start + len(extra)))
            extra += data + bytes(len(data) % 2)
        else:
            entries.append(head + data.ljust(TIFF_INLINE, bytes(1)))
    header = TIFF_HEADER + struct.pack("<I", first_ifd)
    ifd = struct.pack("<H", len(entries)) + b"".join(entries) + struct.pack("<I", 0)
    return header + ifd + extra + strip
