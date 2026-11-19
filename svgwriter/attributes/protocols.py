"""Structural protocols used by attribute serialization."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["SupportsSVG", "TextSink"]


@runtime_checkable
class SupportsSVG(Protocol):
    """Anything that knows how to render itself as an attribute value.

    A runtime-checkable protocol: any object with an ``svg_value`` method matches.

    See Also
    --------
    format_value : Uses the protocol to serialize values.

    Examples
    --------
    >>> from svgwriter.attributes import Length, SupportsSVG
    >>> isinstance(Length(1), SupportsSVG)
    True
    """

    def svg_value(self, precision: int = ...) -> str:
        """Return the text to write into the SVG attribute."""


@runtime_checkable
class TextSink(Protocol):
    """A writable text stream.

    A runtime-checkable protocol: any object with a ``write`` method matches,
    such as an open text file or `io.StringIO`.

    Examples
    --------
    >>> import io
    >>> from svgwriter.attributes import TextSink
    >>> isinstance(io.StringIO(), TextSink)
    True
    """

    def write(self, text: str, /) -> object:
        """Write text to the stream."""
