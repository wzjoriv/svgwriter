"""
``Typeface``: a font family of one or more faces, picked by weight and style as CSS does.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from .._internal._constants import NORMAL_WEIGHT
from .._internal._font_constants import (
    FONT_FILE_SUFFIXES,
)
from .._internal._font_match import FontStyle, match_rank, style_of
from ._constants import DEFAULT_FONT_SIZE
from ._faces import Face, FaceMetrics, css_family
from ._sources import FontSource, family_of, installed_faces, load, load_face
from .text import register_font

__all__ = ["Face", "FaceMetrics", "FontSource", "Typeface", "known_typefaces"]


_REGISTERED: set[tuple[str, Any, Any, str]] = set()
_KNOWN: dict[str, Typeface] = {}


def known_typefaces() -> list[Typeface]:
    """Every typeface made in this session, the latest per family name.

    Returns
    -------
    list of Typeface
        The typefaces :meth:`Document.embed_fonts <svgwriter.Document.embed_fonts>` looks for by default.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.ops.typeface import known_typefaces
    >>> serif = svg.Typeface("serif")
    >>> serif in known_typefaces()
    True
    """
    return list(_KNOWN.values())


class Typeface:
    """A font family: the faces (weights, styles, widths) that share one name.

    Use it wherever a family name goes (``font_family=``, ``font=``, theme
    fonts); text then gets the face that CSS font matching picks for its
    ``font-weight`` and ``font-style``. Faces loaded from files are
    registered for rendering at once, so nothing needs installing.
    :meth:`css` and :meth:`Document.embed_fonts <svgwriter.Document.embed_fonts>`
    write ``@font-face`` rules so saved SVG files carry the fonts.

    This is not :class:`~svgwriter.Font`, the SVG 1.1 ``<font>`` element that
    defines glyphs inside a document.

    Parameters
    ----------
    name : str
        The family name. Alone, it loads the installed family (generic names
        such as ``"serif"`` pick the first installed candidate).
    faces : iterable of path or bytes, or mapping of (weight, style) to path or bytes, optional
        Font files instead of installed fonts. A mapping states each file's
        weight and style itself, overriding what the file says. Defaults to
        None.

    Raises
    ------
    LookupError
        If *faces* is None and no such family is installed.
    ValueError
        If a file is not a font.

    See Also
    --------
    register_font : Register one file (what this does for each face).

    Examples
    --------
    >>> import svgwriter as svg
    >>> sans = svg.Typeface("sans-serif")
    >>> bold = sans.face(weight=700)
    >>> bold.metrics.units_per_em > 0
    True
    >>> label = svg.text("Total", x=0, y=20, font_family=sans, font_weight="bold")
    >>> str(label.computed("font_family")) == str(sans)
    True
    """

    __slots__ = ("_faces", "_installed", "_name")

    def __init__(self, name: str, faces: Iterable[FontSource] | Mapping[tuple[float, str], FontSource] | None = None
                 ) -> None:
        if faces is None:
            self._name, found = installed_faces(name)
            self._faces = tuple(found)
            self._installed = True
            _KNOWN[self._name.lower()] = self
            return
        entries = faces.items() if isinstance(faces, Mapping) else ((None, source) for source in faces)
        self._fill(name, list(entries))

    def _fill(self, name: str, entries: list[tuple[Any, FontSource]]) -> None:
        """Load file faces (with optional ``(weight, style)`` overrides) and register them."""
        if not entries:
            raise ValueError(f"typeface {name!r} needs at least one face")
        self._name, self._installed = name, False
        loaded = []
        for override, source in entries:
            loaded.extend(load_face(name, typeface, override, path, blob) for typeface, path, blob in load(source))
        self._faces = tuple(loaded)
        self.register()
        _KNOWN[name.lower()] = self

    @classmethod
    def from_files(cls, *sources: FontSource, name: str | None = None,
                   faces: Mapping[tuple[float, str], FontSource] | None = None) -> Typeface:
        """A typeface from font files, each face's weight, style and width read from the file.

        Parameters
        ----------
        *sources : path or bytes
            ``.ttf``/``.otf`` files, their contents (bytes, a binary stream or a
            ``data:`` URI), one per face; collections
            (``.ttc``/``.otc``) add every face they hold; variable fonts cover
            their whole axis ranges.
        name : str, optional
            The family name. Defaults to None, which uses the first file's family
            as stored inside it (typographic family first, so "Inter SemiBold"
            files join "Inter").
        faces : mapping of (weight, style) to path or bytes, optional
            More files whose weight and style are given here instead of read.
            Defaults to None.

        Returns
        -------
        Typeface
            The family, registered for rendering.

        Examples
        --------
        >>> import svgwriter as svg
        >>> # inter = svg.Typeface.from_files("Inter-Regular.ttf", "Inter-Bold.ttf", "Inter-Italic.ttf")
        >>> # svg.text("Hi", x=0, y=20, font_family=inter, font_weight=700)
        """
        entries: list[tuple[Any, FontSource]] = [(None, source) for source in sources]
        entries.extend((faces or {}).items())
        if not entries:
            raise ValueError("from_files needs at least one font file")
        typeface = cls.__new__(cls)
        typeface._fill(name or family_of(entries[0][1]), entries)
        return typeface

    @classmethod
    def from_folder(cls, folder: str | os.PathLike[str], name: str | None = None) -> Typeface:
        """A typeface from the font files in a folder.

        Parameters
        ----------
        folder : str or os.PathLike
            The folder; ``.ttf``, ``.otf``, ``.ttc`` and ``.otc`` files are read.
        name : str, optional
            The family to take from the folder. Defaults to None, which
            requires every file to belong to one family.

        Returns
        -------
        Typeface
            The family, registered for rendering.

        Raises
        ------
        ValueError
            If the folder holds no matching fonts, or several families and no *name*.

        Examples
        --------
        >>> import svgwriter as svg
        >>> # brand = svg.Typeface.from_folder("assets/fonts", "Inter")
        """
        files = sorted(path for path in Path(os.fspath(folder)).iterdir() if path.suffix.lower() in FONT_FILE_SUFFIXES)
        families = {path: family_of(path) for path in files}
        if name is not None:
            files = [path for path in files if families[path].lower() == name.lower()]
        elif len(set(families.values())) > 1:
            raise ValueError(f"{folder} holds several families {sorted(set(families.values()))}; pass name=")
        if not files:
            raise ValueError(f"no {name or 'font'} files in {folder}")
        return cls.from_files(*files, name=families[files[0]])

    @property
    def name(self) -> str:
        """The family name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("monospace").name != "monospace"
        True
        """
        return self._name

    @property
    def faces(self) -> tuple[Face, ...]:
        """Every face of the family.

        Examples
        --------
        >>> import svgwriter as svg
        >>> len(svg.Typeface("serif").faces) >= 1
        True
        """
        return self._faces

    @property
    def installed(self) -> bool:
        """Whether the faces come from the system's installed fonts rather than files.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("serif").installed
        True
        """
        return self._installed

    def register(self) -> Typeface:
        """Register every file face with :func:`register_font` (done on construction; repeats are skipped).

        Returns
        -------
        Typeface
            This typeface.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("serif").register().installed
        True
        """
        for face in () if self._installed else self._faces:
            key = (self._name.lower(), face.source or face.blob, face.weight, face.style)
            if key not in _REGISTERED:
                register_font(face.data, self._name,
                              weight=face.weight, style=face.style)
                _REGISTERED.add(key)
        return self

    def face(self, weight: float | str = NORMAL_WEIGHT, style: FontStyle | bool = "normal") -> Face:
        """The face CSS font matching picks for a weight and style.

        Parameters
        ----------
        weight : float or {"normal", "bold"}, optional
            The requested weight. Defaults to 400.
        style : {"normal", "italic", "oblique"} or bool, optional
            The requested style (True means italic). Defaults to "normal".

        Returns
        -------
        Face
            The nearest face; a variable face comes back pinned to *weight*.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("sans-serif").face(weight="bold").weight[0] >= 400
        True
        """
        from .._internal._fonts import font_weight

        wanted, slant = float(font_weight(weight)), style_of(style)
        chosen = min(self._faces, key=lambda face: match_rank(face, wanted, slant))
        return chosen.at(wanted) if chosen.weight[0] != chosen.weight[1] else chosen

    def measure(self, text: str, size: float = DEFAULT_FONT_SIZE, *, weight: float | str = NORMAL_WEIGHT,
                style: FontStyle | bool = "normal") -> float:
        """Shaped advance width of *text* in the face picked for *weight* and *style*.

        Parameters
        ----------
        text : str
            The characters.
        size : float, optional
            Font size in user units. Defaults to 16.0.
        weight : float or {"normal", "bold"}, optional
            Font weight. Defaults to 400.
        style : {"normal", "italic", "oblique"} or bool, optional
            Font style. Defaults to "normal".

        Returns
        -------
        float
            The width in user units.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("serif").measure("Hello", 20) > 0
        True
        """
        return self.face(weight, style).measure(text, size)

    def css(self, faces: Iterable[Face] | None = None, *, embed: bool = True) -> str:
        """``@font-face`` rules, the font files embedded as data URIs or referenced.

        Parameters
        ----------
        faces : iterable of Face, optional
            The faces to write. Defaults to None, which writes every face.
        embed : bool, optional
            Embed the files. Defaults to True; False writes ``local(...)`` for
            installed faces and ``url(path)`` for file faces, so an SVG kept
            next to its fonts stays small.

        Returns
        -------
        str
            One rule per face, newline-separated.

        Examples
        --------
        >>> import svgwriter as svg
        >>> sans = svg.Typeface("sans-serif")
        >>> sans.css([sans.face()]).count("@font-face")
        1
        """
        return "\n".join(face.css(embed=embed) for face in (self._faces if faces is None else faces))

    def svg_value(self, precision: int | None = None) -> str:
        """The family name as a ``font-family`` value (quoted when CSS needs it).

        Parameters
        ----------
        precision : int, optional
            Unused; accepted so every attribute value shares one signature.

        Returns
        -------
        str
            The family name.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Typeface("serif").svg_value() == str(svg.Typeface("serif"))
        True
        """
        return css_family(self._name)

    def __str__(self) -> str:
        return css_family(self._name)

    def __repr__(self) -> str:
        return f"Typeface({self._name!r}, {len(self._faces)} faces)"

    def __iter__(self) -> Iterator[Face]:
        return iter(self._faces)

    def __len__(self) -> int:
        return len(self._faces)
