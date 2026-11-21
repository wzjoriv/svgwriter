"""
TIFF out: RGBA, or CMYK through an ICC profile for print.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._constants import PX_PER_INCH
from .._registry import register

if TYPE_CHECKING:
    from ..._internal._color._icc_output import IccLike
    from ...color.color import ColorLike
    from ...document import Document

__all__ = ["tiff"]


@register("tiff", extensions=(".tif", ".tiff"))
def tiff(document: Document, *, scale: float = 1.0, size: tuple[int, int] | int | None = None, padding: float = 0.0,
         background: ColorLike | None = None, dpi: float | None = None, icc: IccLike | None = None) -> bytes:
    """TIFF: lossless RGBA, or CMYK separations through a CMYK ICC profile.

    Parameters
    ----------
    document : Document
        The drawing.
    scale, size, padding, background : optional
        As for PNG. A CMYK file has no transparency, so `background` defaults to white for it.
    dpi : float, optional
        Pixels per inch instead of `scale` (96 is scale 1); written as the file's resolution.
        Defaults to None.
    icc : {"srgb", "display-p3"} or bytes, optional
        Output profile, embedded in the file: ``"srgb"`` tags the pixels as sRGB,
        ``"display-p3"`` or RGB profile bytes convert them, and CMYK profile bytes (a press or
        printer profile) write CMYK ink. Needs the ``color`` extra. Defaults to None, untagged sRGB.

    Returns
    -------
    bytes
        The TIFF file, deflate-compressed.

    Raises
    ------
    ImportError
        If `icc` is given without the ``color`` extra.
    ValueError
        If `icc` is not a readable RGB or CMYK profile.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(8, 4)
    >>> _ = doc.rect(0, 0, 8, 4, fill="teal")
    >>> svg.export.export(doc, "tiff", dpi=300)[:4]
    b'II*\\x00'
    """
    from ..._internal._rgba import to_uint8
    from ..._internal._tiff import encode_tiff

    if dpi is not None:
        scale = dpi / PX_PER_INCH
    if isinstance(size, int):
        size = (size, size)
    target = None
    if icc is not None:
        from ..._internal._color._icc_output import output_profile

        target = output_profile(icc)
    cmyk = target is not None and target.space == "CMYK"
    if cmyk and background is None:
        background = "white"
    pixels = to_uint8(document.rasterize(scale=scale, size=size, padding=padding, background=background))
    if target is not None:
        from ..._internal._color._icc_output import to_profile

        pixels = to_profile(pixels, target)
    return encode_tiff(pixels, "CMYK" if cmyk else "RGB", dpi=scale * PX_PER_INCH,
                       profile=None if target is None else target.data)
