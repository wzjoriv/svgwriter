"""
``Preview``: a project's output files as one HTML page, for notebooks and the live preview server.
"""

from __future__ import annotations

import base64
import html
import warnings
from collections.abc import Sequence
from pathlib import Path

from ._constants import GALLERY_STYLE, IMAGE_TYPES, KILOBYTE, VIDEO_TYPES

__all__ = ["Preview", "gallery"]


def _data_uri(mime: str, data: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _visuals(path: Path) -> list[str]:
    """HTML showing *path*: the image or video itself, or each page read back as SVG."""
    suffix = path.suffix.lower()
    if suffix in IMAGE_TYPES:
        return [f'<img src="{_data_uri(IMAGE_TYPES[suffix], path.read_bytes())}" alt="{html.escape(path.name)}">']
    if suffix in VIDEO_TYPES:
        return [f'<video src="{_data_uri(VIDEO_TYPES[suffix], path.read_bytes())}" autoplay loop muted controls></video>']
    from ...document import Document

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pages = Document.open_all(path)
    except (ValueError, ImportError, OSError):
        return []
    return [f'<img src="{_data_uri(IMAGE_TYPES[".svg"], page.to_string().encode("utf-8"))}" '
            f'alt="{html.escape(path.name)} page {index}">' for index, page in enumerate(pages, 1)]


def gallery(paths: Sequence[Path], title: str = "") -> str:
    """One HTML fragment with a captioned tile per output file."""
    tiles = []
    for path in paths:
        caption = f"{html.escape(path.name)} <small>{path.stat().st_size / KILOBYTE:.1f} KB</small>"
        tiles.append(f'<figure>{"".join(_visuals(path))}<figcaption>{caption}</figcaption></figure>')
    heading = f"<h3>{html.escape(title)}</h3>" if title else ""
    body = "".join(tiles) or "<p>No outputs.</p>"
    return f'<div class="svgwriter-preview"><style>{GALLERY_STYLE}</style>{heading}{body}</div>'


class Preview:
    """A project's output files shown inline: images play, SVG animations run, PDF and PowerPoint pages appear as drawings.

    Notebooks display it as HTML; :attr:`paths` lists the files.

    Parameters
    ----------
    paths : sequence of pathlib.Path
        The files to show.
    title : str, optional
        A heading above them. Defaults to ``""``.

    See Also
    --------
    svgwriter.Project.preview : Builds the project and returns one.

    Examples
    --------
    >>> from svgwriter.tools.project import Preview
    >>> Preview([])._repr_html_().endswith("<p>No outputs.</p></div>")
    True
    """

    def __init__(self, paths: Sequence[Path], title: str = "") -> None:
        self.paths = list(paths)
        self.title = title

    def __repr__(self) -> str:
        return f"<Preview of {len(self.paths)} files: {', '.join(path.name for path in self.paths)}>"

    def _repr_html_(self) -> str:
        return gallery(self.paths, self.title)
