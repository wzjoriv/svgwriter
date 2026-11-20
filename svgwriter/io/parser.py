"""
Read SVG text back into the element model using ``xml.etree``.
"""

from __future__ import annotations

import enum
import warnings
import xml.etree.ElementTree as ET
from typing import Final

from .._internal._constants import SVG_NS, XLINK_NS, XML_NS
from .._internal._typing import AnyPath
from ..attributes.names import UNSUPPORTED_ATTRIBUTES
from ..elements.core import Category, ContentModel, Element, UnknownElement

__all__ = ["SVGParseError", "Strictness", "parse", "parse_file"]

_PREFIXES: Final = {XLINK_NS: "xlink", XML_NS: "xml"}


class Strictness(enum.IntEnum):
    """How to treat unknown elements and unsupported attributes while parsing.

    Members are ordered by severity, so they compare as integers.

    Attributes
    ----------
    LENIENT : int
        Accept everything silently; unknown elements become generic elements.
    WARN : int
        Accept everything but emit a warning for each problem.
    STRICT : int
        Raise :class:`SVGParseError` on the first problem.

    See Also
    --------
    parse : Parse SVG text using one of these levels.

    Examples
    --------
    >>> from svgwriter.io import Strictness
    >>> Strictness.STRICT > Strictness.LENIENT
    True
    """

    LENIENT = 0
    WARN = 1
    STRICT = 2


class SVGParseError(ValueError):
    """Raised for malformed input or, when strict, unsupported content.

    Subclasses :class:`ValueError`.

    See Also
    --------
    parse : The function that raises it.

    Examples
    --------
    >>> from svgwriter.io import SVGParseError, parse
    >>> try:
    ...     parse("<svg")
    ... except SVGParseError:
    ...     print("malformed")
    malformed
    """


def _split(name: str) -> tuple[str | None, str]:
    if name.startswith("{"):
        namespace, _, local = name[1:].partition("}")
        return namespace, local
    return None, name


def _complain(message: str, strictness: Strictness) -> None:
    if strictness is Strictness.STRICT:
        raise SVGParseError(message)
    if strictness is Strictness.WARN:
        warnings.warn(message, stacklevel=4)


def _keeps_whitespace(element: Element) -> bool:
    return element.category is Category.TEXT_CONTENT or element.content is ContentModel.TEXT


def _add_text(element: Element, text: str | None) -> None:
    if not text or (not text.strip() and not _keeps_whitespace(element)):
        return
    if element.children and isinstance(element.children[-1], str):
        element.children[-1] += text
    else:
        element.children.append(text)


def _convert(node: ET.Element, strictness: Strictness) -> Element:
    namespace, local = _split(node.tag)
    attributes: dict[str, str] = {}
    for key, value in node.attrib.items():
        key_ns, key_local = _split(key)
        if key_ns is None and key_local in UNSUPPORTED_ATTRIBUTES:
            _complain(f"dropping unsupported scripting attribute {key_local!r} on <{local}>", strictness)
        elif key_ns is None:
            attributes[key_local] = value
        elif key_ns in _PREFIXES:
            attributes[f"{_PREFIXES[key_ns]}:{key_local}"] = value
        else:
            attributes[key] = value
    if "href" in attributes:
        plain = attributes.pop("href")
        attributes.setdefault("xlink:href", plain)

    cls = Element.lookup(local) if namespace in (SVG_NS, None) else None
    element: Element
    if cls is None:
        if namespace in (SVG_NS, None):
            _complain(f"unknown SVG element <{local}>", strictness)
        element = UnknownElement(local, namespace=None if namespace == SVG_NS else namespace)
        element.attributes.update(attributes)
    else:
        element = cls.from_attributes(attributes)

    _add_text(element, node.text)
    for child_node in node:
        child = _convert(child_node, strictness)
        child.parent = element
        element.children.append(child)
        _add_text(element, child_node.tail)
    return element


def parse(source: str | bytes, *, strictness: Strictness = Strictness.LENIENT) -> Element:
    """Parse SVG text into an element tree.

    Reads the text with ``xml.etree`` and rebuilds it with the library's element
    classes, so the result can be edited and written back out.

    Parameters
    ----------
    source : str or bytes
        The document. A DOCTYPE and XML declaration are accepted.
    strictness : Strictness, optional
        What to do with unknown elements and unsupported attributes. Defaults to
        ``Strictness.LENIENT``.

    Returns
    -------
    Element
        The root, usually an :class:`~svgwriter.elements.Svg`.

    Raises
    ------
    SVGParseError
        If the text is not well-formed XML, its root is not an SVG element, or,
        when strict, it contains unknown elements or scripting attributes.

    See Also
    --------
    parse_file : Parse from a file path.

    Examples
    --------
    >>> from svgwriter.io import parse
    >>> root = parse('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="1" cy="2" r="3"/></svg>')
    >>> type(root).__name__, root.children
    ('Svg', [<Circle circle cx='1' cy='2' r='3'>])
    >>> type(parse('<circle r="2"/>')).__name__
    'Circle'
    """
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise SVGParseError(str(exc)) from exc
    element = _convert(root, strictness)
    if isinstance(element, UnknownElement):
        raise SVGParseError(f"<{element.tag}> is not an SVG element; expected <svg> or an SVG fragment such as <g>")
    return element


def parse_file(path: AnyPath, *, strictness: Strictness = Strictness.LENIENT) -> Element:
    """Parse an SVG file.

    Reads the file as bytes, so the encoding declared in the XML prolog is honored.

    Parameters
    ----------
    path : str or os.PathLike
        The file to read.
    strictness : Strictness, optional
        What to do with unknown elements and unsupported attributes. Defaults to
        ``Strictness.LENIENT``.

    Returns
    -------
    Element
        The root, usually an :class:`~svgwriter.elements.Svg`.

    Raises
    ------
    SVGParseError
        If the content is malformed or, when strict, unsupported.
    FileNotFoundError
        If `path` does not exist.

    See Also
    --------
    parse : Parse from text instead of a file.

    Examples
    --------
    >>> import tempfile, pathlib
    >>> from svgwriter.io import parse_file
    >>> with tempfile.TemporaryDirectory() as folder:
    ...     path = pathlib.Path(folder) / "a.svg"
    ...     _ = path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    ...     print(type(parse_file(path)).__name__)
    Svg
    """
    with open(path, "rb") as handle:
        return parse(handle.read(), strictness=strictness)
