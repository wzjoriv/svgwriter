"""
HTML pages holding the drawing as inline SVG, with optional event handlers that live in the page only.
"""

from __future__ import annotations

import html
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ._constants import PAGE, SCRIPT, SVG_RE
from ._registry import register, register_importer

if TYPE_CHECKING:
    from ..document import Document

__all__ = ["html_page", "read_html"]


@register("html", extensions=(".html", ".htm"), binary=False)
def html_page(document: Document, *, title: str | None = None, background: str = "white", css: str = "",
              handlers: Mapping[str, Mapping[str, str]] | None = None) -> str:
    """A standalone HTML page showing the drawing as inline SVG.

    The SVG itself stays static: event handlers are attached by a small
    script in the page, by element id, so the same drawing still exports
    cleanly to every other format.

    Parameters
    ----------
    document : Document
        The drawing.
    title : str, optional
        Page title. Defaults to None, which uses the document's ``<title>`` or "svgwriter".
    background : str, optional
        CSS page background. Defaults to "white".
    css : str, optional
        Extra CSS for the page (it can style SVG elements by id or class). Defaults to "".
    handlers : mapping, optional
        ``{element_id: {event: javascript}}``; the code runs with ``event``
        and ``this`` bound to the element, for example
        ``{"logo": {"click": "this.style.opacity = 0.5"}}``. Defaults to None.

    Returns
    -------
    str
        The HTML text.

    Raises
    ------
    ValueError
        If a handler names an id that is not in the document.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(40, 20)
    >>> _ = doc.rect(0, 0, 40, 20, id="box", fill="teal")
    >>> page = svg.export.export(doc, "html", handlers={"box": {"click": "this.style.fill = 'red'"}})
    >>> page.startswith("<!doctype html>"), "addEventListener" in page
    (True, True)
    """
    events = {key: dict(value) for key, value in (handlers or {}).items()}
    missing = [key for key in events if document.root.get_element_by_id(key) is None]
    if missing:
        raise ValueError(f"handlers name ids not in the document: {', '.join(missing)}")
    heading = title
    if heading is None:
        found = document.root.find("title")
        heading = found.text_content if found is not None and found.text_content else "svgwriter"
    script = SCRIPT.format(handlers=json.dumps(events).replace("</", "<\\/")) if events else ""
    return PAGE.format(title=html.escape(heading), background=background, css=css,
                       svg=document.to_string(xml_declaration=False), script=script)


@register_importer("html", extensions=(".html", ".htm"))
def read_html(data: bytes) -> Document:
    """The first inline ``<svg>`` of an HTML page as a document.

    Parameters
    ----------
    data : bytes
        The page (UTF-8).

    Returns
    -------
    Document
        The drawing; page scripts and styles are not kept.

    Raises
    ------
    ValueError
        If the page has no inline ``<svg>``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.circle(5, 5, 4)
    >>> [e.tag for e in read_html(svg.export.export(doc, "html").encode())]
    ['circle']
    """
    from ..document import Document

    found = SVG_RE.search(data.decode("utf-8", "replace"))
    if found is None:
        raise ValueError("the page has no inline <svg>")
    markup = found.group(0)
    if "xmlns=" not in markup.split(">", 1)[0]:
        markup = markup.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return Document.from_string(markup)
