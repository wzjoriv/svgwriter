"""
TIFF out: RGBA, or CMYK through an ICC profile for print.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..._internal._constants import PX_PER_INCH
from .._registry import register
from .._units import dpi_scale

if TYPE_CHECKING:
    from ..._internal._color._icc_output import IccLike
    from ...document import Document
    from ...model.color.color import ColorLike

__all__ = ["tiff"]


@register("tiff", extensions=(".tif", ".tiff"))
def tiff(document: Document, *, scale: float = 1.0, pixels: tuple[int, int] | int | None = None, padding: float = 0.0,
         background: ColorLike | None = None, dpi: float | None = None,
         units_per_inch: float = PX_PER_INCH, icc: IccLike | None = None) -> bytes:
    """TIFF: lossless RGBA, or CMYK separations through a CMYK ICC profile.

    Parameters
    ----------
    document : Document
        The drawing.
    scale, pixels, padding, background : optional
        As for PNG. A CMYK file has no transparency, so `background` defaults to white for it.
    dpi : float, optional
        Pixels per printed inch instead of `scale`; written as the file's resolution. Defaults to None.
    units_per_inch : float, optional
        User units per inch of a page sized in plain numbers: 72 makes one unit one point. Sizes in
        ``mm``, ``cm``, ``in``, ``pt`` or ``pc`` are kept. Defaults to 96 (CSS).
    icc : {"srgb", "display-p3"} or bytes, optional
        Output profile, embedded in the file: ``"srgb"`` tags the pixels as sRGB,
        ``"display-p3"`` or RGB profile bytes convert them, and CMYK profile bytes (a press or
        printer profile) write CMYK ink. Defaults to None, untagged sRGB.

    Returns
    -------
    bytes
        The TIFF file, deflate-compressed.

    Raises
    ------
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
    from ..._internal._codecs._rgba import to_uint8
    from ..._internal._codecs._tiff import encode_tiff

    if dpi is not None:
        scale = dpi_scale(document, dpi, units_per_inch)
    if isinstance(pixels, int):
        pixels = (pixels, pixels)
    target = None
    if icc is not None:
        from ..._internal._color._icc_output import output_profile

        target = output_profile(icc)
    cmyk = target is not None and target.space == "CMYK"
    if cmyk and background is None:
        background = "white"
    image = to_uint8(document.rasterize(scale=scale, pixels=pixels, padding=padding, background=background))
    if target is not None:
        from ..._internal._color._icc_output import to_profile

        image = to_profile(image, target)
    return encode_tiff(image, "CMYK" if cmyk else "RGB", dpi=dpi if dpi is not None else scale * PX_PER_INCH,
                       profile=None if target is None else target.data)
