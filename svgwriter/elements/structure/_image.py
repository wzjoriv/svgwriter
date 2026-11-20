"""
``<image>`` backed by numpy pixels: color channels plus a broadcastable alpha.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import numpy as np

from ...attributes.length import LengthLike
from ...attributes.viewbox import PreserveAspectRatio
from ...pathdata.data import BBox
from .._behavior._mixins import GraphicsElement, XLinkAttributes
from .._behavior._viewport import Positioned, positioned_bbox
from ..core._element import Category, ContentModel
from ._compositing import Compositing
from ._constants import DATA_URI_PREFIX, HREF
from ._pixels import Pixels

if TYPE_CHECKING:
    pass

__all__ = ["Image"]


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
        format : {"png", "jpeg", "webp", "bmp", "gif", "ppm"}, optional
            Output format. Defaults to ``"png"``.
        quality : int, optional
            Compression quality for lossy formats; ignored by BMP, GIF and PPM. Defaults to 90.

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
