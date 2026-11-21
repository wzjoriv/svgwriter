"""
File formats: one class per format declares its name, extensions and how it reads and writes documents.
"""

from __future__ import annotations

import difflib
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Final

from ..._internal._constants import SUGGESTIONS
from ..._internal._registry import Registry
from ...errors import UnknownNameError
from ._constants import DEFAULT_PAGE_OPTION, EXTENSION_DOT

if TYPE_CHECKING:
    from ...document import Document

__all__ = ["FORMATS", "Format", "FormatRegistry"]


def _extensions(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(e.lower() if e.startswith(EXTENSION_DOT) else EXTENSION_DOT + e.lower() for e in values)


class Format:
    """A file format: subclass it to add one, and :data:`FORMATS` finds it by name or extension.

    Declare the format in the class line and define :meth:`write`, :meth:`read` or both; the class registers
    itself when it is created, and ``doc.save``, ``svg.export.export``, ``Document.open`` and
    ``Document.from_string`` use it from then on.

    Parameters
    ----------
    name : str
        The format name, given as ``format=`` (stored lower-case).
    extensions : tuple of str, optional
        File extensions that select the format for reading and writing; when two formats list one, the
        format that lists it first wins (``.jpg``, ``.jpeg``). Defaults to ().
    read_extensions : tuple of str, optional
        Further extensions that select the format for reading only (``(".json",)``). Defaults to ().
    binary : bool, optional
        Whether :meth:`write` returns ``bytes`` (otherwise ``str``). Defaults to True.
    multipage : bool, optional
        Whether :meth:`write` also takes a list of documents (one page or slide each) and :meth:`read`
        returns a list when its page option is None. Defaults to False.
    page_option : str, optional
        The option of :meth:`read` that picks one page of a multi-page file. Defaults to ``"page"``.
    replace : bool, optional
        Replace a format already registered under the name, a built-in one included. Defaults to False.

    Attributes
    ----------
    description : str
        The first line of the class docstring, else of the :meth:`write` (or :meth:`read`) docstring.

    See Also
    --------
    FORMATS : Every format by name.

    Notes
    -----
    A class line without ``name=`` makes a base class for formats that share code, not a format.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Count(svg.Format, name="count", extensions=(".count",), binary=False):
    ...     \"\"\"The number of top-level elements.\"\"\"
    ...     def write(self, document, **options):
    ...         return str(len(document))
    ...     def read(self, data, **options):
    ...         doc = svg.Document(10, 10)
    ...         for _ in range(int(data)):
    ...             doc.rect(0, 0, 1, 1)
    ...         return doc
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.circle(5, 5, 2)
    >>> doc.export("count"), len(svg.Document.from_string("3", "count"))
    ('1', 3)
    >>> svg.formats.writer("tally.count").description
    'The number of top-level elements.'
    >>> _ = svg.formats.unregister("count")
    """

    name: ClassVar[str] = ""
    extensions: ClassVar[tuple[str, ...]] = ()
    read_extensions: ClassVar[tuple[str, ...]] = ()
    binary: ClassVar[bool] = True
    multipage: ClassVar[bool] = False
    page_option: ClassVar[str | None] = None

    def __init_subclass__(cls, *, name: str | None = None, extensions: tuple[str, ...] = (),
                          read_extensions: tuple[str, ...] = (), binary: bool = True, multipage: bool = False,
                          page_option: str = DEFAULT_PAGE_OPTION, replace: bool = False, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if name is None:
            return
        cls.name = name.lower()
        cls.extensions = _extensions(extensions)
        cls.read_extensions = _extensions(read_extensions)
        cls.binary = binary
        cls.multipage = multipage
        cls.page_option = page_option if multipage else None
        FORMATS.register(cls(), name=cls.name, replace=replace)

    @property
    def description(self) -> str:
        doc = type(self).__doc__ or (self.write.__doc__ if self.writable else self.read.__doc__) or ""
        lines = doc.strip().splitlines()
        return lines[0] if lines else ""

    @property
    def readable(self) -> bool:
        """Whether the format defines :meth:`read`."""
        return type(self).read is not Format.read

    @property
    def writable(self) -> bool:
        """Whether the format defines :meth:`write`."""
        return type(self).write is not Format.write

    def read(self, data: bytes, **options: Any) -> Document | list[Document]:
        """Parse file contents into a document (a list of them for a multi-page file with no page chosen).

        Parameters
        ----------
        data : bytes
            The file contents.
        **options
            Format options.

        Returns
        -------
        Document or list of Document
            The document.
        """
        raise NotImplementedError(f"the {self.name} format cannot be read")

    def write(self, document: Any, **options: Any) -> bytes | str:
        """Serialize *document* (a list of documents for a multi-page format).

        Parameters
        ----------
        document : Document or list of Document
            What to write.
        **options
            Format options.

        Returns
        -------
        bytes or str
            The file contents: ``bytes`` when the format is binary.
        """
        raise NotImplementedError(f"the {self.name} format cannot be written")

    def __repr__(self) -> str:
        ways = "/".join(way for way, able in (("read", self.readable), ("write", self.writable)) if able)
        return f"<format {self.name} {' '.join(self.extensions)} ({ways})>"


class FormatRegistry(Registry[Format]):
    """The registry of :class:`Format` instances, with lookups by name, extension or file path.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.formats.writer("drawing.pdf").name, svg.formats.reader(".svgz").name
    ('pdf', 'svg')
    >>> {"svg", "png", "pdf"} <= set(svg.formats.writers()), "image" in svg.formats.readers()
    (True, True)
    """

    def writers(self) -> list[str]:
        """The names of the formats that write documents.

        Returns
        -------
        list of str
            The names, built-in ones first.
        """
        return [name for name in self.list() if self.get(name).writable]

    def readers(self) -> list[str]:
        """The names of the formats that read documents.

        Returns
        -------
        list of str
            The names, built-in ones first.
        """
        return [name for name in self.list() if self.get(name).readable]

    def writer(self, key: str | os.PathLike[str]) -> Format:
        """The format that writes a name, an extension (``".pdf"``, ``"pdf"``) or a file path.

        Parameters
        ----------
        key : str or path-like
            A format name, an extension, or a path whose extension selects the format.

        Returns
        -------
        Format
            The matching format.

        Raises
        ------
        UnknownNameError
            If no writable format matches; the message suggests the closest names.
        """
        return self._match(key, "write", lambda found: found.writable, lambda found: found.extensions)

    def reader(self, key: str | os.PathLike[str]) -> Format:
        """The format that reads a name, an extension (``".svg"``, ``"svg"``) or a file path.

        Parameters
        ----------
        key : str or path-like
            A format name, an extension, or a path whose extension selects the format.

        Returns
        -------
        Format
            The matching format.

        Raises
        ------
        UnknownNameError
            If no readable format matches; the message suggests the closest names.
        """
        return self._match(key, "read", lambda found: found.readable,
                           lambda found: found.extensions + found.read_extensions)

    def _match(self, key: str | os.PathLike[str], way: str, able: Callable[[Format], bool],
               extensions: Callable[[Format], tuple[str, ...]]) -> Format:
        """The format *able* to handle *key*: by name, then by its own extension, then by any extension."""
        text = os.fspath(key)
        lowered = text.lower()
        path_like = bool(Path(lowered).suffix) or os.sep in lowered
        suffix = Path(lowered).suffix or (lowered if lowered.startswith(EXTENSION_DOT) else EXTENSION_DOT + lowered)
        candidates: list[Format] = []
        for plugins in (False, True):
            named = None if path_like else self.find(lowered, plugins=plugins)
            if named is not None and able(named):
                return named
            candidates = [found for found in map(self.get, self._names(plugins=plugins)) if able(found)]
            for primary in (True, False):
                for found in candidates:
                    if suffix in (found.extensions[:1] if primary else extensions(found)):
                        return found
        names = sorted({found.name for found in candidates} | {e for found in candidates for e in extensions(found)})
        close = difflib.get_close_matches(suffix if path_like else lowered, names, n=SUGGESTIONS)
        hint = f"; did you mean {' or '.join(map(repr, close))}?" if close else ""
        listing = "readers" if way == "read" else "writers"
        raise UnknownNameError(f"no format can {way} {text!r}{hint} (svg.formats.{listing}() lists them)")


def _load_builtins() -> None:
    from . import _diagram, _html, _office, _plotter, _raster, _scene, _svg, _text, _vector  # noqa: F401


FORMATS: Final = FormatRegistry("format", _load_builtins)
"""Every :class:`Format` by name; ``writer(path)`` and ``reader(path)`` pick one by name or extension."""
