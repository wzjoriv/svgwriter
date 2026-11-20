"""
Serialization and display shared by every element: text, files, notebook output and repr.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._internal._typing import AnyPath
from ..attributes.protocols import TextSink
from ..attributes.values import format_value
from ._constants import INLINE_STYLE, PREVIEW_MIN_PIXELS, PREVIEW_PADDING, PREVIEW_SCALE, REPR_WIDTH

if TYPE_CHECKING:
    pass


class Displayable:
    """Text and notebook output; mixed into :class:`~svgwriter.elements.base.Element`."""

    __slots__ = ()

    def to_string(self, **options: Any) -> str:
        """Serialize to an SVG string; see :class:`svgwriter.io.SerializeOptions`.

        Parameters
        ----------
        **options
            Serialization options such as ``pretty`` or ``xml_declaration``.

        Returns
        -------
        str
            The SVG markup.

        See Also
        --------
        save : Write to a file or stream.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.circle(0, 0, 1).to_string(xml_declaration=False, pretty=False)
        '<circle cx="0" cy="0" r="1"/>'
        """
        from ..io.writer import to_string

        return to_string(self, **options)

    def save(self, target: AnyPath | TextSink, **options: Any) -> None:
        """Write to a path or text stream.

        Parameters
        ----------
        target : path or text stream
            Where to write the SVG markup.
        **options
            Serialization options, as for :meth:`to_string`.

        See Also
        --------
        to_string : Serialize to a string.

        Examples
        --------
        >>> import io
        >>> import svgwriter as svg
        >>> buffer = io.StringIO()
        >>> svg.circle(0, 0, 1).save(buffer, xml_declaration=False, pretty=False)
        >>> buffer.getvalue()
        '<circle cx="0" cy="0" r="1"/>'
        """
        from ..io.writer import write

        write(self, target, **options)

    def _preview(self) -> Any:
        """A copy of this element alone in a fitted document, enlarged to at least 200 px on its longer side."""
        from ..document import Document

        doc = Document()
        doc.add(self.clone())
        doc.fit(padding=PREVIEW_PADDING)
        box = doc.root.view_box
        longest = max(box.width, box.height) if box is not None else 0.0
        if 0 < longest < PREVIEW_MIN_PIXELS:
            zoom = PREVIEW_MIN_PIXELS / longest
            doc.root.set("width", box.width * zoom)
            doc.root.set("height", box.height * zoom)
        return doc

    def _repr_svg_(self) -> str | None:
        """Jupyter display: the element alone in a fitted ``<svg>``; None (text repr) when nothing is drawn."""
        if self.tag == "svg":
            return self.to_string(xml_declaration=False)
        if not self._draws_something():
            return None  # type: ignore[return-value]
        return self._preview().to_string(xml_declaration=False)

    def _repr_html_(self) -> str | None:
        """Jupyter display as inline SVG in the page, so text stays selectable and copyable."""
        markup = self._repr_svg_()
        return f'<div style="{INLINE_STYLE}">{markup}</div>' if markup else None

    def _draws_something(self) -> bool:
        """Whether the element has any visible extent (a zero-radius circle has none)."""
        box = getattr(self, "render_bounds", lambda: None)()
        return box is not None and (box.width > 0 or box.height > 0)

    def _repr_png_(self) -> bytes | None:
        """Jupyter display as PNG, for front ends that do not show SVG; None when there is nothing to draw."""
        if not self._draws_something():
            return None
        try:
            return self._preview().render_png(scale=PREVIEW_SCALE)
        except (TypeError, ValueError):
            return None

    def __str__(self) -> str:
        return self.to_string(xml_declaration=False, pretty=False)

    def __repr__(self) -> str:
        shown = " ".join(f"{k}={format_value(v)!r}" for k, v in self.attributes.items())
        if len(shown) > REPR_WIDTH:
            shown = shown[:REPR_WIDTH].rsplit(" ", 1)[0] + " ..."
        return f"<{type(self).__name__} {self.tag}{' ' + shown if shown else ''}>"
