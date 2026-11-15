"""``<image>`` backed by numpy pixels: color channels plus a broadcastable alpha."""

from __future__ import annotations

import base64
import os
from typing import Any, Final

import numpy as np
import skia

from ..._internal._constants import DEFAULT_PRECISION
from ...attributes.length import LengthLike
from ...attributes.viewbox import PreserveAspectRatio
from ...path.data import BBox
from .._mixins import GraphicsElement, XLinkAttributes
from .._viewport import Positioned, positioned_bbox
from ..base import Category, ContentModel

__all__ = ["Image", "Pixels"]

CHANNEL_MAX: Final = 255.0
DATA_URI_PREFIX: Final = "data:"
HREF: Final = "xlink:href"
_MIME: Final = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}


def _normalize(array: np.ndarray) -> np.ndarray:
    data = np.asarray(array)
    if data.dtype == np.uint8:
        return data.astype(np.float32) / CHANNEL_MAX
    if data.dtype.kind not in "fiub":
        raise TypeError(f"pixels must be numeric, got dtype {data.dtype}")
    data = data.astype(np.float32)
    if data.size and (data.min() < 0.0 or data.max() > 1.0):
        raise ValueError("float pixels must be in 0..1; pass uint8 arrays for 0..255 values")
    return data


class Pixels:
    """Image data: ``color`` ``(H, W, C)`` with ``C`` in {1, 3} and ``alpha`` broadcastable to it.

    Both are ``float32`` in ``0..1``. A fully opaque image keeps ``alpha``
    as the scalar ``1.0``. Written as a PNG ``data:`` URI.
    """

    __slots__ = ("_alpha", "_color", "_source")

    def __init__(self, color: np.ndarray | None, alpha: np.ndarray | float = 1.0, source: str | None = None) -> None:
        self._color = color
        self._alpha = alpha
        self._source = source

    @classmethod
    def from_array(cls, array: object, alpha: object = None) -> Pixels:
        """Split an ``(H, W)``, ``(H, W, 1|2|3|4)`` array (float 0..1 or uint8) into color and alpha."""
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
        """Decode PNG, JPEG, WebP, GIF or BMP bytes."""
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
        self._load()
        assert self._color is not None
        return self._color

    @property
    def alpha(self) -> np.ndarray | float:
        self._load()
        return self._alpha

    @property
    def shape(self) -> tuple[int, int]:
        """``(rows, columns)``."""
        return self.color.shape[:2]  # type: ignore[return-value]

    def rgba(self) -> np.ndarray:
        """``(H, W, 4)`` float32 straight RGBA."""
        color = self.color
        rgb = np.repeat(color, 3, axis=2) if color.shape[2] == 1 else color
        alpha = np.broadcast_to(np.asarray(self.alpha, dtype=np.float32), rgb.shape[:2] + (1,))
        return np.concatenate([rgb, alpha], axis=2)

    def encode(self, format: str = "png", *, quality: int = 90) -> bytes:
        from ...ops.render import encode

        return encode(self.rgba(), format, quality=quality)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pixels):
            return NotImplemented
        if self._color is None and other._color is None:
            return self._source == other._source
        return bool(np.array_equal(self.color, other.color) and np.array_equal(self.alpha, other.alpha))

    __hash__ = None  # type: ignore[assignment]

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
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


class Image(
    GraphicsElement, XLinkAttributes, Positioned, tag="image", category=Category.GRAPHICS, content=ContentModel.ELEMENTS
):
    """``<image>``: embedded pixels (numpy) or a linked file.

    Parameters
    ----------
    source : array, str or None
        A pixel array (``(H, W)``, ``(H, W, 3)`` or ``(H, W, 4)``; floats in
        ``0..1`` or ``uint8``) to embed, or a URL/path to link.
    x, y : length
        Top-left corner.
    width, height : length, optional
        Display size; defaults to the pixel size for embedded images.
    alpha : array or float, optional
        Separate alpha, broadcastable to ``(H, W)``.
    preserve_aspect_ratio : PreserveAspectRatio or str, optional
        How the pixels fit the box.
    **kwargs
        Presentation and other attributes.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> img = svg.Image(np.zeros((2, 3, 3)), x=10)
    >>> img.shape, img.width, img.alpha
    ((2, 3), 3, 1.0)
    >>> img.color[..., 0] = 1.0
    >>> img.rgba()[0, 0].tolist()
    [1.0, 0.0, 0.0, 1.0]

    Notes
    -----
    ``color`` is ``float32`` ``(H, W, C)`` (``C`` is 1 for grayscale, else 3)
    and ``alpha`` is the scalar ``1.0`` when fully opaque, otherwise
    ``(H, W, 1)``, so ``color * alpha`` always broadcasts. Edit them in
    place or assign new arrays. Pixels are written as a PNG ``data:`` URI.
    """

    def __init__(
        self,
        source: np.ndarray | str | None = None,
        x: LengthLike | None = None,
        y: LengthLike | None = None,
        width: LengthLike | None = None,
        height: LengthLike | None = None,
        *,
        alpha: np.ndarray | float | None = None,
        preserve_aspect_ratio: PreserveAspectRatio | str | None = None,
        **kwargs: Any,
    ) -> None:
        href = kwargs.pop("href", None)
        if isinstance(source, str) or source is None:
            href = source if source is not None else href
            super().__init__(href=href, x=x, y=y, width=width, height=height, **kwargs)
        else:
            super().__init__(x=x, y=y, width=width, height=height, **kwargs)
            self.attributes[HREF] = Pixels.from_array(source, alpha)
            self._default_size()
        self.update(preserve_aspect_ratio=preserve_aspect_ratio)

    @classmethod
    def open(cls, path: str | os.PathLike[str], **kwargs: Any) -> Image:
        """Decode an image file (PNG, JPEG, WebP, GIF, BMP) into an embedded ``<image>``."""
        with open(path, "rb") as handle:
            pixels = Pixels.decode(handle.read())
        image = cls(**kwargs)
        image.attributes[HREF] = pixels
        image._default_size()
        return image

    def _default_size(self) -> None:
        rows, columns = self.pixels.shape  # type: ignore[union-attr]
        if self.get("width") is None:
            self.set("width", columns)
        if self.get("height") is None:
            self.set("height", rows)

    @property
    def pixels(self) -> Pixels | None:
        """The embedded :class:`Pixels`, decoding a parsed ``data:`` URI on first use."""
        raw = self.attributes.get(HREF)
        if isinstance(raw, Pixels):
            return raw
        if raw is not None and str(raw).startswith(DATA_URI_PREFIX):
            pixels = Pixels(None, source=str(raw))
            self.attributes[HREF] = pixels
            return pixels
        return None

    def _require(self) -> Pixels:
        pixels = self.pixels
        if pixels is None:
            raise TypeError(f"<image> links to {self.get(HREF)!r} and has no embedded pixels; use Image.open()")
        return pixels

    @property
    def color(self) -> np.ndarray:
        """Color channels, ``float32`` ``(H, W, 1|3)`` in ``0..1``; editable in place."""
        return self._require().color

    @color.setter
    def color(self, value: np.ndarray) -> None:
        self.attributes[HREF] = Pixels.from_array(value, self._require().alpha)

    @property
    def alpha(self) -> np.ndarray | float:
        """Alpha: ``1.0`` when opaque, else ``float32`` ``(H, W, 1)``."""
        return self._require().alpha

    @alpha.setter
    def alpha(self, value: np.ndarray | float) -> None:
        self.attributes[HREF] = Pixels.from_array(self._require().color, value)

    @property
    def shape(self) -> tuple[int, int]:
        """Pixel ``(rows, columns)``."""
        return self._require().shape

    def rgba(self) -> np.ndarray:
        """Combined ``(H, W, 4)`` float32 straight RGBA."""
        return self._require().rgba()

    def encode(self, format: str = "png", *, quality: int = 90) -> bytes:
        """The pixels as PNG, JPEG or WebP bytes."""
        return self._require().encode(format, quality=quality)

    def local_bbox(self) -> BBox | None:
        return positioned_bbox(self)
