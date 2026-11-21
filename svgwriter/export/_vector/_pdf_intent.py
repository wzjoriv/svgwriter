"""
PDF output intents: an ICC profile declaring the colour of the page, added as an incremental update.
"""

from __future__ import annotations

import re
import zlib
from typing import TYPE_CHECKING

from ._constants import (
    OBJECT_RE,
    PDF_ICC_COMPONENTS,
    PDF_OUTPUT_INTENTS,
    PDF_STRING_ESCAPES,
    ROOT_RE,
    STARTXREF_RE,
    TRAILER_INFO_RE,
    TRAILER_SIZE_RE,
)

if TYPE_CHECKING:
    from ..._internal._icc_output import OutputProfile

__all__ = ["with_output_intent"]


def _string(text: str) -> bytes:
    return b"(" + text.translate(PDF_STRING_ESCAPES).encode("latin-1", "replace") + b")"


def _object_body(data: bytes, number: int) -> bytes:
    """The text between ``number 0 obj`` and ``endobj`` of the last definition of an object."""
    starts = [m for m in OBJECT_RE.finditer(data) if int(m.group(1)) == number]
    if not starts:
        raise ValueError(f"the PDF has no object {number}")
    body = data[starts[-1].end():]
    return body[:body.index(b"endobj")].strip()


def with_output_intent(data: bytes, target: OutputProfile) -> bytes:
    """Append an output intent with *target*'s ICC profile to a PDF as an incremental update.

    Parameters
    ----------
    data : bytes
        A PDF with a classic cross-reference table, as skia writes it.
    target : OutputProfile
        The sRGB profile (a PDF/A-style ``GTS_PDFA1`` intent: the page's DeviceRGB colours are
        sRGB) or a CMYK printing profile (a PDF/X-style ``GTS_PDFX`` intent naming the press
        condition the RGB colours are meant for).

    Returns
    -------
    bytes
        The PDF with the profile stream, the intent and a catalog that lists it appended after
        the original bytes, which are left untouched.

    Raises
    ------
    ValueError
        If the profile is not sRGB or CMYK, or the PDF has no catalog.

    Notes
    -----
    Skia writes every colour as DeviceRGB in sRGB, so an RGB intent other than sRGB would
    reinterpret the colours; it is refused rather than silently shifting them.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._icc import lcms_available
    >>> data = svg.export.export(svg.Document(4, 4), "pdf", icc="srgb") if lcms_available() else b"/OutputIntents"
    >>> b"/OutputIntents" in data
    True
    """
    if target.space not in PDF_OUTPUT_INTENTS or (target.space == "RGB" and not target.srgb):
        raise ValueError(f"a PDF output intent must be 'srgb' or a CMYK profile, not {target.name!r} "
                         f"({target.space}): the pages hold sRGB colours")
    tail = data[data.rindex(b"trailer"):]
    root_match, size_match = ROOT_RE.search(tail), TRAILER_SIZE_RE.search(tail)
    if root_match is None or size_match is None:
        raise ValueError("the PDF trailer has no /Root or /Size")
    root, size = int(root_match.group(1)), int(size_match.group(1))
    previous = list(STARTXREF_RE.finditer(tail))[-1].group(2)
    subtype, condition = PDF_OUTPUT_INTENTS[target.space]
    profile = zlib.compress(target.data)
    catalog = re.sub(rb"/OutputIntents\s*\[[^\]]*\]", b"", _object_body(data, root))
    catalog = catalog[:catalog.rindex(b">>")] + b"\n/OutputIntents [%d 0 R]>>" % (size + 1)
    objects = {
        size: b"<</N %d\n/Filter /FlateDecode\n/Length %d>> stream\n" % (PDF_ICC_COMPONENTS[target.space], len(profile))
              + profile + b"\nendstream",
        size + 1: b"<</Type /OutputIntent\n/S /" + subtype + b"\n/OutputConditionIdentifier (" + condition
                  + b")\n/Info " + _string(target.name) + b"\n/DestOutputProfile %d 0 R>>" % size,
        root: catalog,
    }
    out = bytearray(data if data.endswith(b"\n") else data + b"\n")
    offsets = {}
    for number, body in objects.items():
        offsets[number] = len(out)
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n"
    for number in sorted(offsets):
        out += b"%d 1\n%010d 00000 n \n" % (number, offsets[number])
    info = TRAILER_INFO_RE.search(tail)
    out += (b"trailer\n<</Size %d\n/Root %d 0 R\n" % (size + 2, root) + (info.group(0) + b"\n" if info else b"")
            + b"/Prev " + previous + b">>\nstartxref\n%d\n%%%%EOF\n" % xref)
    return bytes(out)
