"""
``<image>`` backed by numpy pixels: color channels plus a broadcastable alpha.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Final

import numpy as np
import skia

from ..._internal._constants import DEFAULT_PRECISION
from ...attributes.length import LengthLike
from ...attributes.viewbox import PreserveAspectRatio
from ...pathdata.data import BBox
from .._mixins import GraphicsElement, XLinkAttributes
from .._viewport import Positioned, positioned_bbox
from ..base import Category, ContentModel
from ._compositing import Compositing

if TYPE_CHECKING:
    from ...ops.composite import Operator

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
            PNG, JPEG, WebP, GIF or BMP file contents.

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
        format : {"png", "jpeg", "webp"}, optional
            Output format. Defaults to ``"png"``.
        quality : int, optional
            Compression quality for lossy formats. Defaults to 90.

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
        from ...ops.render import encode

        return encode(self.rgba(), format, quality=quality)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pixels):
            return NotImplemented
        if self._color is None and other._color is None:
            return self._source == other._source
        return bool(np.array_equal(self.color, other.color) and np.array_equal(self.alpha, other.alpha))

    __hash__ = None  # type: ignore[assignment]

    def composite(self, backdrop: Pixels | np.ndarray, operator: Operator = "over", *, k: Sequence[float] = ()) -> Pixels:
        """Composite these pixels onto *backdrop*, pixel for pixel.

        ``a | b``, ``a & b``, ``a - b`` and ``a ^ b`` are ``over``, ``in``,
        ``out`` and ``xor``.

        Parameters
        ----------
        backdrop : Pixels or numpy.ndarray
            Pixels underneath, or a straight RGBA array; it broadcasts, so
            ``(1, 1, 4)`` is a solid color.
        operator : CompositeOperator, BlendMode or str, optional
            An ``feComposite`` operator or ``feBlend`` mode. Defaults to ``"over"``.
        k : sequence of float, optional
            ``(k1, k2, k3, k4)`` for ``"arithmetic"``. Defaults to ().

        Returns
        -------
        Pixels
            New pixels; both operands are left unchanged.

        Raises
        ------
        ValueError
            If the operator is unknown or the pixel shapes do not broadcast.

        See Also
        --------
        Image.composite : Composite placed images, resampling as needed.

        Examples
        --------
        >>> import numpy as np
        >>> from svgwriter.elements.structure import Pixels
        >>> glass = Pixels.from_array(np.full((2, 2, 3), 1.0), alpha=0.25)
        >>> (glass | np.array([[[0, 0, 0, 1.0]]])).rgba()[0, 0].tolist()
        [0.25, 0.25, 0.25, 1.0]
        """
        from ...ops.composite import composite_rgba

        under = backdrop.rgba() if isinstance(backdrop, Pixels) else np.asarray(backdrop, dtype=np.float32)
        try:
            return Pixels.from_array(composite_rgba(self.rgba(), under, operator, k=k))
        except ValueError as error:
            if "broadcast" not in str(error):
                raise
            raise ValueError(f"pixel shapes {self.shape} and {under.shape[:2]} differ; "
                             "composite the Image elements to resample them onto one canvas") from None

    def _pair(self, other: object, operator: str) -> Pixels:
        return self.composite(other, operator) if isinstance(other, (Pixels, np.ndarray)) else NotImplemented  # type: ignore[return-value]

    def __or__(self, other: object) -> Pixels:
        return self._pair(other, "over")

    def __and__(self, other: object) -> Pixels:
        return self._pair(other, "in")

    def __sub__(self, other: object) -> Pixels:
        return self._pair(other, "out")

    def __xor__(self, other: object) -> Pixels:
        return self._pair(other, "xor")

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


class Image(
    Compositing,
    GraphicsElement, XLinkAttributes, Positioned, tag="image", category=Category.GRAPHICS, content=ContentModel.ELEMENTS
):
    """``<image>``: embedded pixels (numpy) or a linked file.

    Parameters
    ----------
    source : array, str or None, optional
        A pixel array (``(H, W)``, ``(H, W, 3)`` or ``(H, W, 4)``; floats in
        ``0..1`` or ``uint8``) to embed, or a URL/path to link. Defaults to None.
    x, y : length, optional
        Top-left corner. Defaults to None.
    width, height : length, optional
        Display size; defaults to the pixel size for embedded images.
    alpha : array or float, optional
        Separate alpha, broadcastable to ``(H, W)``. Defaults to None.
    preserve_aspect_ratio : PreserveAspectRatio or str, optional
        How the pixels fit the box. Defaults to None.
    **kwargs
        Presentation, core and other SVG attributes in Python spelling.

    See Also
    --------
    Image.open : Embed an image file.
    Pixels : The pixel container behind an embedded image.

    Notes
    -----
    ``color`` is ``float32`` ``(H, W, C)`` (``C`` is 1 for grayscale, else 3)
    and ``alpha`` is the scalar ``1.0`` when fully opaque, otherwise
    ``(H, W, 1)``, so ``color * alpha`` always broadcasts. Edit them in
    place or assign new arrays. Pixels are written as a PNG ``data:`` URI.

    Examples
    --------
    >>> import numpy as np
    >>> import svgwriter as svg
    >>> img = svg.Image(np.zeros((2, 3, 3)), x=10)
    >>> img.shape, img.width, img.alpha
    ((2, 3), 3.0, 1.0)
    >>> img.color[..., 0] = 1.0
    >>> img.rgba()[0, 0].tolist()
    [1.0, 0.0, 0.0, 1.0]
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
        """Decode an image file into an embedded ``<image>``.

        Parameters
        ----------
        path : str or os.PathLike
            A PNG, JPEG, WebP, GIF or BMP file.
        **kwargs
            Attributes for the image, as in the constructor.

        Returns
        -------
        Image
            An image holding the decoded pixels, sized to match them unless
            `width` and `height` are given.

        Raises
        ------
        ValueError
            If the file cannot be decoded.

        Examples
        --------
        >>> import os, tempfile
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     name = os.path.join(folder, "pixel.png")
        ...     _ = open(name, "wb").write(svg.Image(np.zeros((2, 3, 3))).encode())
        ...     svg.Image.open(name).shape
        (2, 3)
        """
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
        """The embedded :class:`Pixels`, or None for a linked image.

        A ``data:`` URI read from a document is decoded on first use.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Image("photo.png").pixels is None
        True
        """
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
        """Color channels, ``float32`` ``(H, W, 1|3)`` in ``0..1``; editable in place.

        Assign an array to replace them.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> img = svg.Image(np.zeros((1, 2, 3)))
        >>> img.color = np.ones((1, 2, 3))
        >>> float(img.color.min())
        1.0
        """
        return self._require().color

    @color.setter
    def color(self, value: np.ndarray) -> None:
        self.attributes[HREF] = Pixels.from_array(value, self._require().alpha)

    @property
    def alpha(self) -> np.ndarray | float:
        """Alpha: ``1.0`` when opaque, else ``float32`` ``(H, W, 1)``.

        Assign a scalar or an array broadcastable to ``(H, W)`` to replace it.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> img = svg.Image(np.zeros((2, 2, 3)))
        >>> img.alpha = 0.5
        >>> img.alpha.shape
        (2, 2, 1)
        """
        return self._require().alpha

    @alpha.setter
    def alpha(self, value: np.ndarray | float) -> None:
        self.attributes[HREF] = Pixels.from_array(self._require().color, value)

    @property
    def shape(self) -> tuple[int, int]:
        """Pixel ``(rows, columns)``.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> svg.Image(np.zeros((2, 3))).shape
        (2, 3)
        """
        return self._require().shape

    def rgba(self) -> np.ndarray:
        """Combine color and alpha into one array.

        Returns
        -------
        numpy.ndarray
            ``(H, W, 4)`` ``float32`` straight (unpremultiplied) RGBA.

        Raises
        ------
        TypeError
            If the image links to a file rather than embedding pixels.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> svg.Image(np.zeros((1, 1, 3))).rgba().tolist()
        [[[0.0, 0.0, 0.0, 1.0]]]
        """
        return self._require().rgba()

    def encode(self, format: str = "png", *, quality: int = 90) -> bytes:
        """Encode the pixels as an image file.

        Parameters
        ----------
        format : {"png", "jpeg", "webp"}, optional
            Output format. Defaults to ``"png"``.
        quality : int, optional
            Compression quality for lossy formats. Defaults to 90.

        Returns
        -------
        bytes
            The encoded file contents.

        Raises
        ------
        TypeError
            If the image links to a file rather than embedding pixels.

        Examples
        --------
        >>> import numpy as np
        >>> import svgwriter as svg
        >>> svg.Image(np.zeros((2, 2, 3))).encode("jpeg")[0]
        255
        """
        return self._require().encode(format, quality=quality)

    def local_bbox(self) -> BBox | None:
        """Box from the ``x``, ``y``, ``width`` and ``height`` attributes.

        Returns
        -------
        BBox or None
            The image rectangle, or None when it has no size.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Image(width=4, height=3).local_bbox()
        BBox(x=0.0, y=0.0, width=4.0, height=3.0)
        >>> svg.Image().local_bbox() is None
        True
        """
        return positioned_bbox(self)
