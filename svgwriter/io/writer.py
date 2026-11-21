"""
Serialization of element trees to SVG text.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import InitVar, dataclass, field
from typing import Any

from .._internal._constants import (
    DEFAULT_INDENT,
    DEFAULT_PRECISION,
    DOCTYPE,
    INKSCAPE_NS,
    KNOWN_NAMESPACES,
    SVG_NS,
)
from .._internal._escape import escape_attribute, escape_text
from .._internal._sentinels import MISSING, MissingType
from .._internal._typing import AnyPath
from ..attributes.protocols import TextSink
from ..attributes.values import format_value
from ..elements.core import Element, UnknownElement
from ..pathdata.data import PathData
from ..transform.matrix import Matrix
from ._constants import DEFAULT_ENCODING, FOREIGN_PREFIX, NAMESPACE_DECLARATION
from ._inkscape import transform_center
from ._markup import default_namespaces, inline_content, open_text, ordered, used_namespaces

__all__ = ["SerializeOptions", "Writer", "iter_chunks", "to_string", "write"]


@dataclass(kw_only=True)
class SerializeOptions:
    """Output settings for serialization.

    All fields are keyword-only. They control layout, number formatting and the
    prolog written before the root element.

    Parameters
    ----------
    pretty : bool, optional
        Indent and break lines; ``False`` writes everything on one line.
        Defaults to True.
    indent : str, optional
        One level of indentation when pretty. Defaults to two spaces.
    precision : int, optional
        Maximum decimals for numbers. Defaults to 4.
    xml_declaration : bool, optional
        Emit ``<?xml ...?>``. Defaults to True.
    doctype : bool, optional
        Emit the SVG 1.1 DOCTYPE. Defaults to False.
    encoding : str, optional
        Declared and used when writing files. Defaults to ``"utf-8"``.
    compact_paths : bool, optional
        Write path data in its shortest form. Defaults to False.
    namespaces : dict, optional
        Namespace declarations put on a root ``<svg>``. Defaults to the SVG and
        XLink namespaces. Other prefixes in use (``inkscape:``, ``sodipodi:``,
        prefixes declared by a parsed file) are declared once on the root too.

    See Also
    --------
    Writer : Applies these options.
    to_string : Serialize with options in one call.

    Examples
    --------
    >>> from svgwriter.io import SerializeOptions
    >>> options = SerializeOptions(pretty=False, precision=2)
    >>> options.indent, options.precision
    ('', 2)
    """

    pretty: InitVar[bool] = True
    indent: str = DEFAULT_INDENT
    precision: int = DEFAULT_PRECISION
    xml_declaration: bool = True
    doctype: bool = False
    encoding: str = DEFAULT_ENCODING
    compact_paths: bool = False
    namespaces: dict[str, str] = field(default_factory=default_namespaces)
    newline: str = field(init=False, default="\n")

    def __post_init__(self, pretty: bool) -> None:
        if not pretty:
            self.indent = ""
            self.newline = ""


class Writer:
    """Turn an element tree into text, honoring :class:`SerializeOptions`.

    Parameters
    ----------
    options : SerializeOptions, optional
        Pre-built options. Defaults to None, in which case `kwargs` build one.
    **kwargs
        Fields of :class:`SerializeOptions`, used when `options` is None.

    See Also
    --------
    to_string : Module-level shortcut.
    write : Module-level shortcut for files and streams.

    Examples
    --------
    >>> from svgwriter import Circle
    >>> from svgwriter.io import Writer
    >>> Writer(pretty=False, xml_declaration=False).to_string(Circle(5, 5, 2))
    '<circle cx="5" cy="5" r="2"/>'
    """

    def __init__(self, options: SerializeOptions | None = None, **kwargs: Any) -> None:
        self.options = options if options is not None else SerializeOptions(**kwargs)

    def _value(self, name: str, value: Any) -> str:
        if self.options.compact_paths and isinstance(value, PathData):
            return value.svg_value(self.options.precision, compact=True)
        return format_value(value, self.options.precision)

    def _transform(self, element: Element, value: Any) -> str:
        """A matrix written relative to the element's own anchor when that reads better."""
        if not isinstance(value, Matrix) or not hasattr(element, "anchor"):
            return self._value("transform", value)
        return value.svg_value(self.options.precision, pivot=element.anchor,
                               box=element.local_bbox())  # type: ignore[attr-defined]

    def _open_tag(self, element: Element, extra: dict[str, str], names: dict[str, str], tag: str) -> str:
        attributes = dict(extra)
        for key, value in ordered(element.attributes):
            if key.startswith("{"):
                namespace, _, local = key[1:].partition("}")
                key = f"{names[namespace]}:{local}"
            elif key in attributes:
                continue
            attributes[key] = self._transform(element, value) if key == "transform" else self._value(key, value)
        if INKSCAPE_NS in names:
            attributes.update({key: self._value(key, value) for key, value in transform_center(element).items()})
        parts = [tag] + [f'{k}="{escape_attribute(v)}"' for k, v in attributes.items()]
        return "<" + " ".join(parts)

    def _namespaces(self, element: Element) -> tuple[dict[str, str], dict[str, str]]:
        """The declarations written on the top element, and each namespace URI's prefix."""
        declared: dict[str, str] = {}
        if element.tag == "svg" and not isinstance(element, UnknownElement):
            declared.update(self.options.namespaces)
        prefixes, attribute_uris, element_uris = used_namespaces(element)
        scope: Element | None = element
        while scope is not None:
            for key, value in scope.attributes.items():
                if key.startswith(NAMESPACE_DECLARATION + ":") and (
                        scope is element or key.partition(":")[2] in prefixes
                        or value in attribute_uris or value in element_uris):
                    declared.setdefault(key, str(value))
            scope = scope.parent
        if "xlink" not in prefixes:
            declared.pop("xmlns:xlink", None)
        for prefix in sorted(prefixes):
            if prefix in KNOWN_NAMESPACES:
                declared.setdefault(f"xmlns:{prefix}", KNOWN_NAMESPACES[prefix])
        names = {uri: key.partition(":")[2] for key, uri in declared.items() if ":" in key}
        known = {uri: prefix for prefix, uri in KNOWN_NAMESPACES.items()}
        for uri in sorted(attribute_uris | element_uris):
            if uri in names or uri == SVG_NS:
                continue
            if uri in known:
                prefix = known[uri]
            elif uri in attribute_uris:
                prefix = next(f"{FOREIGN_PREFIX}{n}" for n in range(len(declared) + 1)
                              if f"xmlns:{FOREIGN_PREFIX}{n}" not in declared)
            else:
                continue
            declared[f"xmlns:{prefix}"] = uri
            names[uri] = prefix
        return declared, names

    def _element(self, element: Element, depth: int, extra: dict[str, str], inline: bool,
                 names: dict[str, str]) -> Iterator[str]:
        opts = self.options
        pad = "" if inline else opts.indent * depth
        namespace = getattr(element, "namespace", None)
        tag = f"{names[namespace]}:{element.tag}" if namespace in names else element.tag
        yield pad + self._open_tag(element, extra, names, tag)
        if not element.children:
            yield "/>"
            return
        yield ">"
        inner_inline = inline or inline_content(element)
        default = None if namespace in names else namespace
        for child in element.children:
            if isinstance(child, str):
                yield escape_text(child)
                continue
            child_ns = getattr(child, "namespace", None)
            declare = {"xmlns": child_ns} if child_ns and child_ns != default and child_ns not in names else {}
            if not inner_inline:
                yield opts.newline
            yield from self._element(child, depth + 1, declare, inner_inline, names)
        if not inner_inline:
            yield opts.newline + pad
        yield f"</{tag}>"

    def iter_chunks(self, element: Element, *, xml_declaration: bool | MissingType = MISSING) -> Iterator[str]:
        """Yield the document in pieces (useful for streaming).

        Joining the chunks gives the same text as :meth:`to_string`.

        Parameters
        ----------
        element : Element
            Root of the tree to write.
        xml_declaration : bool, optional
            Override the ``xml_declaration`` option for this call. Defaults to
            the option's value.

        Yields
        ------
        str
            Consecutive fragments of the document.

        See Also
        --------
        to_string : Join the chunks into one string.

        Examples
        --------
        >>> from svgwriter import Circle
        >>> from svgwriter.io import Writer
        >>> list(Writer(pretty=False, xml_declaration=False).iter_chunks(Circle(5, 5, 2)))
        ['<circle cx="5" cy="5" r="2"', '/>']
        """
        opts = self.options
        declaration = opts.xml_declaration if xml_declaration is MISSING else xml_declaration
        if declaration:
            yield f'<?xml version="1.0" encoding="{opts.encoding}" standalone="no"?>{opts.newline or chr(10)}'
        if opts.doctype:
            yield DOCTYPE + (opts.newline or "\n")
        declared, names = self._namespaces(element)
        yield from self._element(element, 0, declared, False, names)
        if opts.newline:
            yield opts.newline

    def to_string(self, element: Element, **kwargs: Any) -> str:
        """Serialize *element* to a string.

        Parameters
        ----------
        element : Element
            Root of the tree to write.
        **kwargs
            Forwarded to :meth:`iter_chunks` (``xml_declaration``).

        Returns
        -------
        str
            The complete document.

        See Also
        --------
        write : Write to a path or stream instead.

        Examples
        --------
        >>> from svgwriter import Circle
        >>> from svgwriter.io import Writer
        >>> Writer(pretty=False).to_string(Circle(5, 5, 2), xml_declaration=False)
        '<circle cx="5" cy="5" r="2"/>'
        """
        return "".join(self.iter_chunks(element, **kwargs))

    def write(self, element: Element, target: AnyPath | TextSink, **kwargs: Any) -> None:
        """Write to a filesystem path or any object with ``write(str)``.

        Parameters
        ----------
        element : Element
            Root of the tree to write.
        target : str, os.PathLike or TextSink
            Destination path (written with the configured encoding) or text stream.
        **kwargs
            Forwarded to :meth:`iter_chunks` (``xml_declaration``).

        Raises
        ------
        TypeError
            If `target` is neither a path nor a text stream.

        See Also
        --------
        to_string : Return the text instead.

        Examples
        --------
        >>> import io
        >>> from svgwriter import Circle
        >>> from svgwriter.io import Writer
        >>> stream = io.StringIO()
        >>> Writer(pretty=False, xml_declaration=False).write(Circle(5, 5, 2), stream)
        >>> stream.getvalue()
        '<circle cx="5" cy="5" r="2"/>'
        """
        if isinstance(target, (str, os.PathLike)):
            self._write_path(element, target, **kwargs)
        elif isinstance(target, TextSink):
            self._write_stream(element, target, **kwargs)
        else:
            raise TypeError(f"cannot write to {type(target).__name__}")

    def _write_path(self, element: Element, path: AnyPath, **kwargs: Any) -> None:
        with open_text(path, self.options.encoding) as stream:
            self._write_stream(element, stream, **kwargs)

    def _write_stream(self, element: Element, stream: TextSink, **kwargs: Any) -> None:
        for chunk in self.iter_chunks(element, **kwargs):
            stream.write(chunk)


def iter_chunks(element: Element, **kwargs: Any) -> Iterator[str]:
    """Yield the serialized document in pieces.

    Module-level shortcut for :meth:`Writer.iter_chunks`.

    Parameters
    ----------
    element : Element
        Root of the tree to write.
    **kwargs
        Fields of :class:`SerializeOptions`, plus ``xml_declaration`` to override
        the prolog for this call.

    Yields
    ------
    str
        Consecutive fragments of the document.

    See Also
    --------
    to_string : Join the chunks into one string.

    Examples
    --------
    >>> from svgwriter import Circle
    >>> from svgwriter.io import iter_chunks
    >>> list(iter_chunks(Circle(5, 5, 2), pretty=False, xml_declaration=False))
    ['<circle cx="5" cy="5" r="2"', '/>']
    """
    xml_declaration = kwargs.pop("xml_declaration", MISSING)
    return Writer(**kwargs).iter_chunks(element, xml_declaration=xml_declaration)


def to_string(element: Element, *, options: SerializeOptions | None = None, **kwargs: Any) -> str:
    """Serialize *element* to a string.

    Builds a :class:`Writer` from the options and returns its output in one piece.

    Parameters
    ----------
    element : Element
        Root of the tree to write.
    options : SerializeOptions, optional
        Pre-built options; otherwise keywords build one. Defaults to None.
    **kwargs
        Fields of :class:`SerializeOptions` (``pretty``, ``precision``...).

    Returns
    -------
    str
        The complete document.

    See Also
    --------
    write : Write to a path or stream.
    iter_chunks : Stream the text in pieces.

    Examples
    --------
    >>> from svgwriter import Circle
    >>> to_string(Circle(5, 5, 2), xml_declaration=False, pretty=False)
    '<circle cx="5" cy="5" r="2"/>'
    """
    return Writer(options, **kwargs).to_string(element)


def write(element: Element, target: AnyPath | TextSink, **kwargs: Any) -> None:
    """Write *element* to a path or text stream.

    Keywords are the same as in :func:`to_string`.

    Parameters
    ----------
    element : Element
        Root of the tree to write.
    target : str, os.PathLike or TextSink
        Destination path or any object with ``write(str)``.
    **kwargs
        ``options`` or fields of :class:`SerializeOptions`.

    Raises
    ------
    TypeError
        If `target` is neither a path nor a text stream.

    See Also
    --------
    to_string : Return the text instead.
    svgwriter.io.write_async : Write to a path in a worker thread.

    Examples
    --------
    >>> import io
    >>> from svgwriter import Circle
    >>> from svgwriter.io import write
    >>> stream = io.StringIO()
    >>> write(Circle(5, 5, 2), stream, pretty=False, xml_declaration=False)
    >>> stream.getvalue()
    '<circle cx="5" cy="5" r="2"/>'
    """
    options = kwargs.pop("options", None)
    Writer(options, **kwargs).write(element, target)
