"""
Exact page boxes for the PDF files skia writes with whole-point pages.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

from ...._internal._numbers import format_number
from ._constants import MEDIA_BOX_RE, PDF_BOX_PRECISION, STARTXREF_RE, XREF_ENTRY_RE

__all__ = ["exact_media_boxes", "page_points"]


def page_points(width: float, height: float) -> tuple[int, int]:
    """The whole-point page skia draws on: the exact size rounded up so nothing is cut.

    Parameters
    ----------
    width, height : float
        The exact page size in points.

    Returns
    -------
    (int, int)
        Width and height in whole points.

    See Also
    --------
    exact_media_boxes : Trim the pages back to the exact size.

    Examples
    --------
    >>> from svgwriter.formats.export._vector._pdf_boxes import page_points
    >>> page_points(595.28, 841.89)
    (596, 842)
    """
    return math.ceil(width), math.ceil(height)


def exact_media_boxes(data: bytes, sizes: Sequence[tuple[float, float]]) -> bytes:
    """*data* with each page's ``MediaBox`` trimmed to its exact size, the cross-reference table moved to match.

    Skia draws with y flipped about the top of a whole-point page, so the box keeps that top edge
    and the left edge and drops the rounding at the right and bottom.

    Parameters
    ----------
    data : bytes
        A PDF file as skia writes it, pages in order, with a classic ``xref`` table.
    sizes : sequence of (float, float)
        The exact width and height of each page in points.

    Returns
    -------
    bytes
        The PDF file with exact page boxes.

    See Also
    --------
    page_points : The whole-point page skia draws on.

    Examples
    --------
    >>> from svgwriter.formats.export._vector._pdf_boxes import exact_media_boxes
    >>> exact_media_boxes(b"/MediaBox [0 0 596 842]", [(595.28, 841.89)])
    b'/MediaBox [0 0.11 595.28 842]'
    """
    parts, shifts, last = [], [], 0
    for match, (width, height) in zip(MEDIA_BOX_RE.finditer(data), sizes, strict=False):
        top = float(match.group(2))
        box = " ".join(format_number(v, PDF_BOX_PRECISION) for v in (0.0, top - height, width, top))
        replacement = b"/MediaBox [" + box.encode("ascii") + b"]"
        parts += [data[last:match.start()], replacement]
        shifts.append((match.start(), len(replacement) - (match.end() - match.start())))
        last = match.end()
    result = b"".join([*parts, data[last:]])

    def moved(offset: int) -> int:
        return offset + sum(delta for start, delta in shifts if start < offset)

    def entry(match: re.Match[bytes]) -> bytes:
        return b"%010d" % moved(int(match.group(1))) + match.group(2)

    def startxref(match: re.Match[bytes]) -> bytes:
        return match.group(1) + str(moved(int(match.group(2)))).encode("ascii")

    xref = result.rfind(b"\nxref")
    if xref < 0:
        return result
    return result[:xref] + STARTXREF_RE.sub(startxref, XREF_ENTRY_RE.sub(entry, result[xref:]))
