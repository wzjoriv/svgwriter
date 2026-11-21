"""
``Face`` and ``FaceMetrics``: one style of a typeface, its descriptors, metrics and file.
"""

from __future__ import annotations

import base64
import dataclasses
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

import skia

from .._internal._font_constants import AXIS_WEIGHT, FONT_MIME, REGULAR_SUBFAMILY, STANDALONE_SUFFIXES
from .._internal._font_match import FaceStyle, FontStyle, Range, axis_tag
from .._internal._font_names import face_count
from .._internal._sfnt import font_format, sfnt_bytes
from ._constants import DEFAULT_FONT_SIZE, FAMILY_IDENTIFIER

__all__ = ["Face", "FaceMetrics", "css_family"]


def css_family(name: str) -> str:
    """A family name as CSS writes it: bare when it is a plain identifier, single-quoted otherwise."""
    if FAMILY_IDENTIFIER.fullmatch(name):
        return name
    escaped = name.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _span(value: Range, unit: str = "") -> str:
    low, high = (f"{end:g}{unit}" for end in value)
    return low if value[0] == value[1] else f"{low} {high}"


@dataclass(frozen=True)
class FaceMetrics:
    """Vertical metrics of a face, in font units unless scaled with :meth:`at`.

    Parameters
    ----------
    units_per_em : int
        Font units per em.
    ascent : float
        Height above the baseline (positive).
    descent : float
        Depth below the baseline (positive).
    x_height : float
        Height of lowercase ``x``.
    cap_height : float
        Height of flat capitals.

    Examples
    --------
    >>> from svgwriter.ops import FaceMetrics
    >>> FaceMetrics(1000, 800, 200, 500, 700).at(16).ascent
    12.8
    """

    units_per_em: int
    ascent: float
    descent: float
    x_height: float
    cap_height: float

    def at(self, size: float) -> FaceMetrics:
        """The same metrics in user units for a font size; ``units_per_em`` is kept.

        Parameters
        ----------
        size : float
            Font size in user units.

        Returns
        -------
        FaceMetrics
            Ascent, descent, x-height and cap height at that size.

        Examples
        --------
        >>> from svgwriter.ops import FaceMetrics
        >>> FaceMetrics(2048, 1024, 512, 1024, 1536).at(10).cap_height
        7.5
        """
        scale = size / self.units_per_em
        return FaceMetrics(self.units_per_em, self.ascent * scale, self.descent * scale,
                           self.x_height * scale, self.cap_height * scale)


@dataclass(frozen=True)
class Face:
    """One face of a :class:`~svgwriter.ops.Typeface`: a font file and the styles it covers.

    Faces are made by :class:`~svgwriter.ops.Typeface`; read them from
    :attr:`Typeface.faces` or pick one with :meth:`Typeface.face`. A
    variable face covers a weight (and stretch) range; :meth:`Typeface.face`
    returns it pinned to the requested weight.

    Attributes
    ----------
    family : str
        The family name text uses to reach this face.
    weight : (float, float)
        The weights covered; equal ends for a static face.
    style : {"normal", "italic", "oblique"}
        The style.
    stretch : (float, float)
        The widths covered, in percent of normal.
    axes : dict of str to (float, float, float)
        Variation axes by tag (``"wght"``, ``"wdth"``, ``"slnt"``, ...) as
        ``(minimum, default, maximum)``; empty for a static face.
    source : pathlib.Path or None
        The file the face came from; None for installed or in-memory fonts.
    subfamily : str
        The style name inside the font (typographic name first), such as ``"SemiBold Italic"``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> face = svg.Typeface("sans-serif").face(weight=700)
    >>> face.measure("Hi", 20) > 0
    True
    """

    family: str
    weight: Range
    style: FontStyle
    stretch: Range
    axes: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    source: Path | None = None
    subfamily: str = REGULAR_SUBFAMILY
    typeface: Any = field(default=None, repr=False, compare=False)
    blob: bytes | None = field(default=None, repr=False, compare=False)

    @classmethod
    def of(cls, family: str, typeface: Any, described: FaceStyle, source: Path | None = None,
           blob: bytes | None = None, subfamily: str = REGULAR_SUBFAMILY) -> Face:
        """A face from a skia typeface and its CSS descriptors.

        Parameters
        ----------
        family : str
            The family name.
        typeface : skia.Typeface
            The loaded font.
        described : FaceStyle
            Its weight, style, stretch and axes.
        source : pathlib.Path, optional
            The file it was read from. Defaults to None.
        blob : bytes, optional
            The file contents, when already read. Defaults to None.
        subfamily : str, optional
            The style name read from the font. Defaults to "Regular".

        Returns
        -------
        Face
            The face.

        Examples
        --------
        >>> import skia
        >>> from svgwriter._internal._font_match import describe
        >>> from svgwriter.ops import Face
        >>> typeface = skia.Typeface("sans-serif")
        >>> Face.of("Sans", typeface, describe(typeface)).family
        'Sans'
        """
        return cls(family, described.weight, described.style, described.stretch, dict(described.axes),
                   source, subfamily, typeface, blob)

    @property
    def variable(self) -> bool:
        """Whether the face has variation axes.

        Examples
        --------
        >>> import svgwriter as svg
        >>> isinstance(svg.Typeface("serif").face().variable, bool)
        True
        """
        return bool(self.axes)

    @property
    def styles(self) -> frozenset[str]:
        """The styles the face can draw: its own, plus ``oblique`` when a ``slnt`` axis leans.

        Examples
        --------
        >>> import svgwriter as svg
        >>> "normal" in svg.Typeface("serif").face().styles
        True
        """
        return FaceStyle(self.weight, self.style, self.stretch, self.axes).styles

    @cached_property
    def data(self) -> bytes:
        """The font file, rebuilt from the loaded tables for installed fonts and collections.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("sans-serif").face().data[:4] in (b"\\0\\1\\0\\0", b"OTTO", b"true")
        True
        """
        standalone = self.source is None or self.source.suffix.lower() in STANDALONE_SUFFIXES
        if self.blob is not None and standalone and face_count(self.blob) == 1:
            return self.blob
        return sfnt_bytes(self.typeface)

    @property
    def format(self) -> str:
        """``"opentype"`` for CFF outlines, else ``"truetype"`` (the ``@font-face`` format hint).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("sans-serif").face().format in ("truetype", "opentype")
        True
        """
        return font_format([str(axis_tag(tag)) for tag in self.typeface.getTableTags()])

    @cached_property
    def metrics(self) -> FaceMetrics:
        """Units per em, ascent, descent, x-height and cap height, in font units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> metrics = svg.Typeface("sans-serif").face().metrics
        >>> metrics.ascent > metrics.x_height > 0
        True
        """
        units = self.typeface.getUnitsPerEm()
        found = skia.Font(self.typeface, units).getMetrics()
        return FaceMetrics(units, *(round(value) for value in (-found.fAscent, found.fDescent, found.fXHeight, found.fCapHeight)))

    def at(self, weight: float) -> Face:
        """This face pinned to one weight of its range (a variable instance).

        Parameters
        ----------
        weight : float
            The weight; clamped to the face's range.

        Returns
        -------
        Face
            The same file with a single weight.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("sans-serif").face().at(400).weight[0] > 0
        True
        """
        pinned = min(max(float(weight), self.weight[0]), self.weight[1])
        return dataclasses.replace(self, weight=(pinned, pinned))

    def measure(self, text: str, size: float = DEFAULT_FONT_SIZE) -> float:
        """Shaped advance width of *text* set in this face.

        Parameters
        ----------
        text : str
            The characters.
        size : float, optional
            Font size in user units. Defaults to 16.0.

        Returns
        -------
        float
            The width in user units (font fallback and complex-script shaping included).

        Examples
        --------
        >>> import svgwriter as svg
        >>> face = svg.Typeface("sans-serif").face()
        >>> face.measure("WW", 20) > face.measure("ii", 20)
        True
        """
        from .text import text_width

        weight = self.axes[AXIS_WEIGHT][1] if AXIS_WEIGHT in self.axes and self.weight[0] != self.weight[1] \
            else self.weight[0]
        return text_width(text, css_family(self.family), size, weight=round(weight), italic=self.style != "normal")

    def css(self, *, embed: bool = True) -> str:
        """An ``@font-face`` rule for this face.

        Parameters
        ----------
        embed : bool, optional
            Carry the font file as a data URI. Defaults to True; False writes
            ``local('Family Style')`` for an installed face and ``url(path)``
            for a file face (in-memory faces are always embedded).

        Returns
        -------
        str
            The rule, with weight, style and stretch descriptors (ranges for variable faces).

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("sans-serif").face().css(embed=False).count("local(")
        1
        """
        family = self.family.replace("\\", "\\\\").replace('"', '\\"')
        return (f'@font-face {{ font-family: "{family}"; src: {self._src(embed)}; '
                f"font-weight: {_span(self.weight)}; font-style: {self.style}; "
                f"font-stretch: {_span(self.stretch, '%')}; }}")

    def _src(self, embed: bool) -> str:
        """The ``src`` descriptor: a data URI, a local name or the file's URL."""
        if not embed and self.source is not None:
            return f'url("{self.source.as_posix()}") format("{self.format}")'
        if not embed and self.blob is None:
            local = f"{self.family} {self.subfamily}".replace("'", "\\'")
            return f"local('{local}')"
        encoded = base64.b64encode(self.data).decode("ascii")
        return f'url(data:{FONT_MIME[self.format]};base64,{encoded}) format("{self.format}")'
