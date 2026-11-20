"""
Plain text and Markdown in: lines and blocks as ``<text>`` elements in one group.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._constants import (
    BODY_SIZE,
    BOLD_RE,
    BULLET,
    BULLET_RE,
    CODE_FILL,
    HEADING_RE,
    HEADING_SIZES,
    INDENT_PER_LEVEL,
    INLINE_RE,
    LINE_HEIGHT,
    MARGIN,
    MONOSPACE,
    NUMBERED_RE,
    SANS,
    SPACES_PER_LEVEL,
)
from ._registry import register_importer

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.structure import Group

__all__ = ["read_markdown", "read_text"]


def _document(group: Group) -> Document:
    from ..document import Document

    doc = Document()
    doc.add(group)
    return doc.fit(padding=MARGIN)


def read_text(data: bytes) -> Document:
    """A plain-text file as one ``<text>`` per line (spaces kept), stacked in a group.

    Parameters
    ----------
    data : bytes
        UTF-8 text (a BOM is ignored).

    Returns
    -------
    Document
        The lines in a sans-serif 16-unit font, sized to fit.

    Examples
    --------
    >>> doc = read_text(b"first line\\nsecond line")
    >>> [line.text_content for line in doc[0]]
    ['first line', 'second line']
    """
    from ..elements.structure import Group
    from ..elements.text._text import Text

    group = Group(font_family=SANS, font_size=BODY_SIZE)
    y = BODY_SIZE
    for line in data.decode("utf-8-sig").splitlines():
        if line.strip():
            group.add(Text(line, x=0, y=y, xml_space="preserve"))
        y += BODY_SIZE * LINE_HEIGHT
    return _document(group)


register_importer("text", extensions=(".txt", ".text"))(read_text)


def _plain(text: str) -> str:
    """Markdown inline markup removed (code, emphasis, links keep their text)."""
    return INLINE_RE.sub(lambda m: next(g for g in m.groups() if g is not None), text)


def _runs(text: str, **base: object) -> list[object]:
    """``**bold**`` spans as bold ``<tspan>`` runs, the rest as plain strings."""
    from ..elements.text._text import TSpan

    parts: list[object] = []
    position = 0
    for match in BOLD_RE.finditer(text):
        if match.start() > position:
            parts.append(_plain(text[position:match.start()]))
        parts.append(TSpan(_plain(match.group(1) or match.group(2)), font_weight="bold"))
        position = match.end()
    if position < len(text):
        parts.append(_plain(text[position:]))
    return parts or [""]


def read_markdown(data: bytes) -> Document:
    """A Markdown file as styled text: headings sized by level, bullets, bold runs and monospace code blocks.

    Only the text survives; images and tables are reduced to their text,
    links to their label. Lines are not re-wrapped.

    Parameters
    ----------
    data : bytes
        UTF-8 Markdown.

    Returns
    -------
    Document
        One ``<text>`` per line or heading, stacked in a group and sized to fit.

    Examples
    --------
    >>> doc = read_markdown(b"# Title\\n\\nSome **bold** text\\n\\n- item")
    >>> [(t.text_content, t.get("font-size")) for t in doc[0]]
    [('Title', 32.0), ('Some bold text', None), ('• item', None)]
    """
    from ..elements.structure import Group
    from ..elements.text._text import Text

    group = Group(font_family=SANS, font_size=BODY_SIZE)
    y = 0.0
    in_code = False
    for line in data.decode("utf-8-sig").splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        size, x, content, extra = BODY_SIZE, 0.0, line, {}
        if in_code:
            extra = {"font_family": MONOSPACE, "fill": CODE_FILL, "xml_space": "preserve"}
            runs: list[object] = [line]
        elif heading := HEADING_RE.match(line):
            size = HEADING_SIZES[len(heading.group(1))]
            extra = {"font_size": size, "font_weight": "bold"}
            runs = _runs(heading.group(2))
        elif bullet := BULLET_RE.match(line):
            x = len(bullet.group(1)) // SPACES_PER_LEVEL * INDENT_PER_LEVEL
            runs = [BULLET, *_runs(bullet.group(2))]
        elif numbered := NUMBERED_RE.match(line):
            x = len(numbered.group(1)) // SPACES_PER_LEVEL * INDENT_PER_LEVEL
            runs = [f"{numbered.group(2)}. ", *_runs(numbered.group(3))]
        else:
            content = line.strip()
            runs = _runs(content) if content else []
        y += size * LINE_HEIGHT
        if runs and any(str(getattr(r, "text_content", r)).strip() for r in runs):
            group.add(Text(*runs, x=x, y=y, **extra))  # type: ignore[arg-type]
    return _document(group)


register_importer("markdown", extensions=(".md", ".markdown"))(read_markdown)
