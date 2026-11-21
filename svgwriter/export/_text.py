"""
Plain text and Markdown in: lines and blocks as ``<text>`` elements in one group.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
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
    from ..model.elements.core import Element
    from ..model.elements.structure import Group

__all__ = ["Figure", "Line", "read_markdown", "read_text", "stack"]


@dataclass(frozen=True)
class Line:
    """One laid-out line of styled text.

    Attributes
    ----------
    runs : tuple of object
        Strings and ``<tspan>`` runs, in reading order; empty for a blank line.
    size : float
        Font size that sets the line's advance, in user units.
    indent : float
        Left offset in user units.
    style : Mapping of str to object
        Presentation attributes for the ``<text>``.

    Examples
    --------
    >>> Line(("hi",)).size
    16.0
    """

    runs: tuple[object, ...]
    size: float = BODY_SIZE
    indent: float = 0.0
    style: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Figure:
    """A block (a picture or a shape) taking *height* in the text flow.

    Attributes
    ----------
    height : float
        Vertical space the block takes, in user units.
    make : Callable[[float], Element]
        Builds the element with its top edge at the given y.

    Examples
    --------
    >>> from svgwriter.model.elements.shapes import Rect
    >>> Figure(10, lambda y: Rect(0, y, 10, 10)).make(5).get("y")
    5
    """

    height: float
    make: Callable[[float], Element]


def stack(blocks: Iterable[Line | Figure], gap: float = 0.0) -> Group:
    """Lines and figures stacked top to bottom in one sans-serif group.

    Parameters
    ----------
    blocks : iterable of Line or Figure
        The flow, in reading order. Blank lines advance without drawing.
    gap : float, optional
        Space left above each figure, in user units. Defaults to 0.

    Returns
    -------
    Group
        One ``<text>`` per line with text and one element per figure.

    Examples
    --------
    >>> group = stack([Line(("a",)), Line(()), Line(("b",))])
    >>> [round(t.get("y"), 1) for t in group]
    [22.4, 67.2]
    """
    from ..model.elements.structure import Group
    from ..model.elements.text import Text

    group = Group(font_family=SANS, font_size=BODY_SIZE)
    y = 0.0
    for block in blocks:
        if isinstance(block, Figure):
            y += gap
            group.add(block.make(y))
            y += block.height
            continue
        y += block.size * LINE_HEIGHT
        if any(str(getattr(run, "text_content", run)).strip() for run in block.runs):
            group.add(Text(*block.runs, x=block.indent, y=y, **block.style))  # type: ignore[arg-type]
    return group


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
    from ..model.elements.structure import Group
    from ..model.elements.text import Text

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
    from ..model.elements.text import TSpan

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
    lines: list[Line] = []
    in_code = False
    for line in data.decode("utf-8-sig").splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            lines.append(Line((line,), style={"font_family": MONOSPACE, "fill": CODE_FILL, "xml_space": "preserve"}))
        elif heading := HEADING_RE.match(line):
            size = HEADING_SIZES[len(heading.group(1))]
            lines.append(Line(tuple(_runs(heading.group(2))), size, style={"font_size": size, "font_weight": "bold"}))
        elif bullet := BULLET_RE.match(line):
            indent = len(bullet.group(1)) // SPACES_PER_LEVEL * INDENT_PER_LEVEL
            lines.append(Line((BULLET, *_runs(bullet.group(2))), indent=indent))
        elif numbered := NUMBERED_RE.match(line):
            indent = len(numbered.group(1)) // SPACES_PER_LEVEL * INDENT_PER_LEVEL
            lines.append(Line((f"{numbered.group(2)}. ", *_runs(numbered.group(3))), indent=indent))
        else:
            content = line.strip()
            lines.append(Line(tuple(_runs(content)) if content else ()))
    return _document(stack(lines))


register_importer("markdown", extensions=(".md", ".markdown"))(read_markdown)
