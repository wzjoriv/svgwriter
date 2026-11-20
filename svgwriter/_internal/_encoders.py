"""
Pure-numpy BMP, GIF and PNM encoders, and a PNM decoder.
"""

from __future__ import annotations

import struct
from collections.abc import Callable
from typing import Final

import numpy as np

from ._constants import (
    BMP_BI_BITFIELDS,
    BMP_BITS_PER_PIXEL,
    BMP_FILE_HEADER_SIZE,
    BMP_LCS_SRGB,
    BMP_MAGIC,
    BMP_MASKS,
    BMP_PIXELS_PER_METER,
    BMP_V4_HEADER_SIZE,
)
from ._gif import encode_gif
from ._pnm import encode_pnm
from ._rgba import _check_rgba

__all__ = ["ENCODERS", "encode_bmp"]


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


ENCODERS: Final[dict[str, Callable[[np.ndarray], bytes]]] = {
    "bmp": encode_bmp,
    "gif": encode_gif,
    "ppm": encode_pnm,
}
