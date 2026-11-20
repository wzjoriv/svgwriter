"""
Numpy pixel storage for ``<image>``: color channels plus a separate alpha plane.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

import numpy as np
import skia

from ..._internal._constants import DEFAULT_PRECISION
from ..._internal._drawable import Drawable, pixels_picture
from ._constants import CHANNEL_MAX, DATA_URI_PREFIX
from ._pixel_compositing import PixelCompositing

if TYPE_CHECKING:
    pass

__all__ = ["Pixels"]


def _normalize(array: np.ndarray) -> np.ndarray:
    data = np.asarray(array)
    if data.dtype == np.uint8:
        return data.astype(np.float32) / CHANNEL_MAX
    if data.dtype.kind not in "fiub":
        raise TypeError(f"pixels must be numeric, got dtype {data.dtype}")
    if data.dtype.kind in "iu" and data.size and (data.min() < 0 or data.max() > 1):
        raise ValueError(f"{data.dtype} pixels must be 0/1 masks, uint8 (0..255) or floats in 0..1; "
                         "convert with array.astype(np.uint8) or scale to 0..1")
    data = data.astype(np.float32)
    if data.size and (data.min() < 0.0 or data.max() > 1.0):
        raise ValueError("float pixels must be in 0..1; pass uint8 arrays for 0..255 values")
    return data


class Pixels(PixelCompositing, Drawable):
    """Image data: color channels plus a broadcastable alpha.

    ``color`` is ``(H, W, C)`` with ``C`` in {1, 3} and ``alpha`` broadcasts
    to it. Both are ``float32`` in ``0..1``. A fully opaque image keeps
    ``alpha`` as the scalar ``1.0``. Written as a PNG ``data:`` URI.

    Parameters
    ----------
    color : numpy.ndarray or None
        ``float32`` ``(H, W, 1|3)`` color channels; None when the pixels are
        still an undecoded ``data:`` URI.
    alpha : numpy.ndarray or float, optional
        Opacity, ``1.0`` or an array broadcastable to ``color``. Defaults to 1.0.
    source : str, optional
        The ``data:`` URI to decode lazily when `color` is None. Defaults to None.

    See Also
    --------
    Image : The ``<image>`` element holding pixels.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.elements.structure import Pixels
    >>> Pixels.from_array(np.zeros((2, 3, 3)))
    Pixels(2x3, channels=3, opaque=True)
    """

    __slots__ = ("_alpha", "_color", "_source")

    def __init__(self, color: np.ndarray | None, alpha: np.ndarray | float = 1.0, source: str | None = None) -> None:
        self._color = color
        self._alpha = alpha
        self._source = source

    @classmethod
    def from_array(cls, array: object, alpha: object = None) -> Pixels:
        """Create pixels from an array, splitting off any embedded alpha channel.

        Parameters
        ----------
        array : array-like
            ``(H, W)`` or ``(H, W, 1|2|3|4)`` values, floats in ``0..1`` or
            ``uint8``. Two and four channels carry alpha last.
        alpha : array-like or float, optional
            Separate alpha broadcastable to ``(H, W)``. Defaults to None.

        Returns
        -------
        Pixels
            The color and alpha as ``float32`` arrays.

        Raises
        ------
        ValueError
            If the shape is unsupported, float values leave ``0..1``, or
            alpha is given both in `array` and as `alpha`.
        TypeError
            If the array is not numeric.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> px = Pixels.from_array(np.zeros((1, 2, 4)))
        >>> px.color.shape, px.alpha.shape
        ((1, 2, 3), (1, 2, 1))
        """
        data = _normalize(np.asarray(array))
        if data.ndim == 2:
            data = data[..., None]
        if data.ndim != 3 or data.shape[2] not in (1, 2, 3, 4):
            raise ValueError(f"expected (H, W) or (H, W, 1-4) pixels, got shape {data.shape}")
        color, embedded = (data[..., :-1], data[..., -1:]) if data.shape[2] in (2, 4) else (data, None)
        if alpha is not None:
            if embedded is not None:
                raise ValueError("alpha given twice: in the array and as alpha=")
            given = _normalize(np.asarray(alpha))
            if given.ndim == 2:
                given = given[..., None]
            embedded = np.broadcast_to(given, color.shape[:2] + (1,))
        return cls(np.ascontiguousarray(color), _compact_alpha(embedded))

    @classmethod
    def decode(cls, data: bytes) -> Pixels:
        """Decode encoded image bytes.

        Parameters
        ----------
        data : bytes
            PNG, JPEG, WebP, GIF, BMP or PNM file contents.

        Returns
        -------
        Pixels
            The decoded pixels.

        Raises
        ------
        ValueError
            If the data is damaged or in an unknown format.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> png = Pixels.from_array(np.zeros((2, 2, 3))).encode()
        >>> Pixels.decode(png)
        Pixels(2x2, channels=3, opaque=True)
        """
        from ..._internal._pnm import decode_pnm, is_pnm

        if is_pnm(data):
            return cls.from_array(decode_pnm(data))
        encoded = skia.Data.MakeWithCopy(data)
        try:
            codec = skia.Codec.MakeFromData(encoded)
        except RuntimeError:
            codec = None
        if codec is None:
            raise ValueError("could not decode the image data: unknown or damaged format")
        size = codec.getInfo()
        info = skia.ImageInfo.Make(size.width(), size.height(), skia.kRGBA_8888_ColorType, skia.kUnpremul_AlphaType)
        rgba = np.zeros((size.height(), size.width(), 4), np.uint8)
        if codec.getPixels(info, rgba, info.minRowBytes()) != skia.Codec.Result.kSuccess:
            raise ValueError("could not decode the image data")
        return cls.from_array(rgba)

    def _load(self) -> None:
        if self._color is None:
            assert self._source is not None
            loaded = Pixels.decode(_data_uri_bytes(self._source))
            self._color, self._alpha = loaded._color, loaded._alpha

    @property
    def color(self) -> np.ndarray:
        """Color channels, ``float32`` ``(H, W, 1|3)`` in ``0..1``; editable in place.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> pixels = Pixels.from_array(np.zeros((2, 3, 3)))
        >>> pixels.color.shape
        (2, 3, 3)
        """
        self._load()
        assert self._color is not None
        return self._color

    @property
    def alpha(self) -> np.ndarray | float:
        """Alpha: ``1.0`` when opaque, else ``float32`` ``(H, W, 1)``.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> Pixels.from_array(np.zeros((2, 3, 3))).alpha
        1.0
        >>> Pixels.from_array(np.zeros((2, 3, 3)), alpha=0.5).alpha.shape
        (2, 3, 1)
        """
        self._load()
        return self._alpha

    @property
    def shape(self) -> tuple[int, int]:
        """Pixel ``(rows, columns)``.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> Pixels.from_array(np.zeros((2, 3, 3))).shape
        (2, 3)
        """
        return self.color.shape[:2]  # type: ignore[return-value]

    def rgba(self) -> np.ndarray:
        """Combine color and alpha into one array.

        Returns
        -------
        numpy.ndarray
            ``(H, W, 4)`` ``float32`` straight (unpremultiplied) RGBA;
            grayscale is expanded to three channels.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> Pixels.from_array(np.ones((1, 1))).rgba().tolist()
        [[[1.0, 1.0, 1.0, 1.0]]]
        """
        color = self.color
        rgb = np.repeat(color, 3, axis=2) if color.shape[2] == 1 else color
        alpha = np.broadcast_to(np.asarray(self.alpha, dtype=np.float32), rgb.shape[:2] + (1,))
        return np.concatenate([rgb, alpha], axis=2)

    def clone(self) -> Pixels:
        """Copy the pixel arrays.

        Returns
        -------
        Pixels
            An independent copy; editing it leaves this one unchanged.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> px = Pixels.from_array(np.zeros((1, 1, 3)))
        >>> px.clone() == px
        True
        """
        if self._color is None:
            return Pixels(None, source=self._source)
        alpha = self._alpha if np.isscalar(self._alpha) else np.array(self._alpha)
        return Pixels(np.array(self._color), alpha)

    def encode(self, format: str = "png", *, quality: int = 90) -> bytes:
        """Encode the pixels as an image file.

        Parameters
        ----------
        format : {"png", "jpeg", "webp", "bmp", "gif", "ppm"}, optional
            Output format. Defaults to ``"png"``.
        quality : int, optional
            Compression quality for lossy formats; ignored by BMP, GIF and PPM. Defaults to 90.

        Returns
        -------
        bytes
            The encoded file contents.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> Pixels.from_array(np.zeros((2, 2, 3))).encode()[1:4]
        b'PNG'
        """
        from ..._internal._encoders import ENCODERS
        from ..._internal._rgba import to_uint8
        from ...ops.render import encode

        encoder = ENCODERS.get(format.lower())
        if encoder is not None:
            return encoder(to_uint8(self.rgba()))
        return encode(self.rgba(), format, quality=quality)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pixels):
            return NotImplemented
        if self._color is None and other._color is None:
            return self._source == other._source
        return bool(np.array_equal(self.color, other.color) and np.array_equal(self.alpha, other.alpha))

    __hash__ = None  # type: ignore[assignment]

    def __svgwriter__(self) -> Any:
        """Return the pixels as an ``<image>`` for ``doc.add(pixels)`` and notebook display.

        Returns
        -------
        Image
            A new ``<image>`` at the pixel size.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> Pixels.from_array(np.zeros((2, 3, 3))).__svgwriter__().tag
        'image'
        """
        return pixels_picture(self)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize as a ``data:`` URI.

        Parameters
        ----------
        precision : int, optional
            Unused; present for the attribute-value protocol. Defaults to
            the library default.

        Returns
        -------
        str
            A base64 PNG ``data:`` URI, or the original URI if never decoded.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> Pixels.from_array(np.zeros((1, 1, 3))).svg_value()[:30]
        'data:image/png;base64,iVBORw0K'
        """
        if self._color is None and self._source is not None:
            return self._source
        return f"{DATA_URI_PREFIX}image/png;base64," + base64.b64encode(self.encode("png")).decode("ascii")

    def __repr__(self) -> str:
        rows, columns = self.shape
        return f"Pixels({rows}x{columns}, channels={self.color.shape[2]}, opaque={np.isscalar(self.alpha)})"


def _compact_alpha(alpha: np.ndarray | None) -> np.ndarray | float:
    if alpha is None:
        return 1.0
    if alpha.size and float(alpha.min()) == 1.0:
        return 1.0
    return np.ascontiguousarray(alpha, dtype=np.float32)


def _data_uri_bytes(uri: str) -> bytes:
    header, _, payload = uri.partition(",")
    if ";base64" not in header:
        raise ValueError("only base64 data URIs can be decoded")
    return base64.b64decode(payload)
