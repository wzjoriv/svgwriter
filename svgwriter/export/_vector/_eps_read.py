"""
Reading EPS and PostScript drawings back into a document with a small stack machine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...transform.matrix import Matrix
from ._eps_machine import _Machine
from ._eps_syntax import _bounding_box, _parse, _postscript
from ._reading import to_document

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["read_eps"]


def read_eps(data: bytes) -> Document:
    """Read the paths, images and text an EPS or PostScript program paints as elements.

    Parameters
    ----------
    data : bytes
        The PostScript program, optionally inside a DOS EPS binary wrapper.

    Returns
    -------
    Document
        The drawing in points with y pointing down, sized to ``%%HiResBoundingBox``
        or ``%%BoundingBox`` when present and fitted to the content otherwise.

    Raises
    ------
    ValueError
        If *data* does not start with ``%!``.

    See Also
    --------
    svgwriter.export._vector._pdf_read.read_pdf : Read PDF pages.

    Notes
    -----
    A tokenizer and stack machine for a subset of PostScript: numbers, names,
    literal names, strings, arrays and procedures ``{}`` with ``def``,
    ``bind``, ``load`` and ``exec``; dictionaries (``dict``, ``<<``/``>>``,
    ``begin``, ``end``, ``currentdict``) for scoping definitions; the path operators ``moveto lineto
    curveto rmoveto rlineto rcurveto closepath newpath arc arcn``; painting
    with ``fill eofill stroke rectfill rectstroke``; ``setrgbcolor setgray
    setcmykcolor``; ``setlinewidth setlinecap setlinejoin setmiterlimit
    setdash``; ``gsave grestore save restore translate scale rotate concat``;
    and ``dup pop exch add sub mul div neg``. Reading stops at the first
    ``showpage``. Unknown operators are ignored and an operator that finds
    too few operands is skipped, so a program using more of the language
    reads as far as this subset reaches.

    Also read: 8-bit ``image`` (gray, five operands) and ``colorimage``
    (gray, RGB, CMYK; one source or one per component) from ``currentfile``
    with ``/ASCIIHexDecode filter`` or from procedures returning strings,
    placed as ``<image>`` through the current transform and the image
    matrix; text with ``findfont scalefont makefont setfont selectfont`` and
    ``show ashow widthshow awidthshow xyshow`` as ``<text>`` at the current
    point (family from the font name, ``-Bold``/``-Italic`` as weight and
    style, advance from the measured width); and ``clip``/``eoclip``,
    intersected with the current clip and kept by ``gsave``/``grestore``
    (``eoclip`` clips with the nonzero rule). Image data inline in a
    procedure body, other bit depths and image dictionaries are skipped, as
    is control flow (``if``, ``loop``, ...).

    Examples
    --------
    >>> from svgwriter.export._vector._eps_read import read_eps
    >>> doc = read_eps(b"%!PS\\n%%BoundingBox: 0 0 10 10\\n1 0 0 setrgbcolor 0 0 10 5 rectfill")
    >>> doc[0].get("fill"), doc[0].bounds()
    ('#ff0000', BBox(x=0.0, y=5.0, width=10.0, height=5.0))
    """
    data = _postscript(data)
    box = _bounding_box(data)
    llx, lly, urx, ury = box if box is not None else (0.0, 0.0, 0.0, 0.0)
    machine = _Machine(Matrix(1.0, 0.0, 0.0, -1.0, -llx, ury))
    machine.execute(_parse(data))
    return to_document(machine.shapes, None if box is None else (0.0, 0.0, urx - llx, ury - lly))
