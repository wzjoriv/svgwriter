"""
Document output: text, notebook display, rendering, files, formats and animation.
"""

from __future__ import annotations

import os
from pathlib import Path as FilePath
from typing import TYPE_CHECKING, Any, TypeVar

import numpy as np

from .._internal._drawable import ascii_markup
from .._internal._typing import AnyPath
from ..elements.core import Element
from ..video.animation import DEFAULT_FPS
from ._constants import INLINE_STYLE

if TYPE_CHECKING:
    from ..attributes.protocols import TextSink
    from ..color.color import ColorLike
    from ..document import Document
    from ..video.animation import Renderer, Update


E = TypeVar("E", bound=Element)


class Output:
    """Serialization, rendering, saving and loading; mixed into :class:`~svgwriter.Document`."""

    def to_string(self, **options: Any) -> str:
        """Serialize; see :class:`svgwriter.io.SerializeOptions`. Auto-sized documents get their size here.

        Parameters
        ----------
        **options
            Fields of :class:`~svgwriter.io.SerializeOptions`.

        Returns
        -------
        str
            The SVG text.

        See Also
        --------
        save : Write to a file or stream.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document(10, 10)
        >>> _ = doc.circle(5, 5, 2)
        >>> print(doc.to_string(pretty=False, xml_declaration=False))
        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10" version="1.1"><circle cx="5" cy="5" r="2"/></svg>
        """
        with self._prepared():
            return self.root.to_string(**options)

    def __str__(self) -> str:
        return self.to_string(xml_declaration=False)

    def _repr_svg_(self) -> str:
        return ascii_markup(self.to_string(xml_declaration=False))

    def _repr_html_(self) -> str:
        """Jupyter display as inline SVG, so text in the drawing stays selectable and copyable."""
        return f'<div style="{INLINE_STYLE}">{self._repr_svg_()}</div>'

    def at(self, seconds: float) -> Document:
        """A static copy with every SMIL animation applied at *seconds* (and removed).

        Parameters
        ----------
        seconds : float
            Seconds since the document began.

        Returns
        -------
        Document
            The frame at that moment; this document is unchanged.

        See Also
        --------
        render_animation : Uses this for each frame, so SMIL plays without ``update``.

        Notes
        -----
        Supports ``animate``, ``set``, ``animateColor``, ``animateTransform``
        and ``animateMotion`` with clock timing, ``repeatCount``,
        ``repeatDur``, ``fill="freeze"``, ``values``/``from``/``to``/``by``,
        ``keyTimes``, discrete mode and ``additive="sum"``. Event-based begins
        and spline timing are treated as their clock-based, linear equivalents.

        Examples
        --------
        >>> import svgwriter as svg
        >>> doc = svg.Document(100, 20)
        >>> ball = doc.circle(10, 10, 5)
        >>> _ = ball.append(svg.Animate(attribute_name="cx", from_=10, to=90, dur=2))
        >>> doc.at(1.0)[0].get("cx")
        '50'
        """
        from .._internal._animation._smil import snapshot

        return snapshot(self, seconds)

    def _repr_png_(self) -> bytes:
        return self.render_png()

    def rasterize(self, *, scale: float = 1.0, size: tuple[int, int] | int | None = None, padding: float = 0.0,
                  background: ColorLike | None = None, snapshot: bool = False) -> np.ndarray:
        """Render into a float32 RGBA array (see :func:`svgwriter.ops.rasterize`).

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        size : (int, int) or int, optional
            Output size in pixels as ``(width, height)``, or one int for a square. Defaults to None, which
            uses the document size times `scale`.
        padding : float, optional
            Margin around the content, in user units. Defaults to 0.0.
        background : str, optional
            Background color. Defaults to None (transparent).
        snapshot : bool, optional
            Render a copy of the tree. Defaults to False.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(height, width, 4)``.

        See Also
        --------
        render_png : Encode the result as PNG bytes.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document()
        >>> _ = doc.circle(0, 0, 10)
        >>> doc.rasterize(size=(64, 64), padding=2).shape
        (64, 64, 4)
        """
        from ..ops.render import rasterize

        with self._prepared():
            return rasterize(self, scale=scale, size=size, padding=padding, background=background,
                             snapshot=snapshot)

    def render_png(self, *, scale: float = 1.0, background: ColorLike | None = None) -> bytes:
        """Render to PNG bytes.

        Parameters
        ----------
        scale : float, optional
            Pixels per user unit. Defaults to 1.0.
        background : str, optional
            Background color. Defaults to None (transparent).

        Returns
        -------
        bytes
            A PNG file.

        See Also
        --------
        rasterize : The pixels without encoding.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document(8, 6)
        >>> doc.render_png()[1:4]
        b'PNG'
        """
        from ..ops.render import encode_image

        return encode_image(self.rasterize(scale=scale, background=background, snapshot=True))

    def save(self, target: AnyPath | TextSink, *, format: str | None = None, **options: Any) -> None:
        """Write to a path or text stream; the format follows *format* or the file extension.

        ``.svg`` (and text streams) write SVG text with :class:`~svgwriter.io.SerializeOptions`;
        other extensions use :mod:`svgwriter.export` (``.png``, ``.pdf``, ``.tikz``, ...).

        Parameters
        ----------
        target : str, os.PathLike or TextSink
            Destination path or text stream.
        format : str, optional
            Format name or extension. Defaults to None, which follows the
            extension of `target`, or SVG for streams.
        **options
            Serializer or exporter options.

        See Also
        --------
        export : Return the output instead of writing it.
        to_string : The SVG text.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document(10, 10)
        >>> doc.save("figure.pdf")  # doctest: +SKIP
        """
        if format is None and (not isinstance(target, (str, os.PathLike))
                               or str(target).lower().endswith(".svg")):
            with self._prepared():
                self.root.save(target, **options)
            return
        from ..export import save

        save(self, target, format, **options)  # type: ignore[arg-type]

    def export(self, format: str, **options: Any) -> bytes | str:
        """This document in *format* (``"png"``, ``"pdf"``, ``"tikz"``, ... or an extension).

        See :func:`svgwriter.export.exporters` for the registered formats.

        Parameters
        ----------
        format : str
            Format name or extension.
        **options
            Exporter options.

        Returns
        -------
        bytes or str
            The encoded document; text formats return ``str``.

        See Also
        --------
        save : Write to a file.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> Document(10, 10).export("png")[1:4]
        b'PNG'
        """
        from ..export import export

        return export(self, format, **options)

    @classmethod
    def open(cls, path: AnyPath, *, format: str | None = None, **options: Any) -> Document:
        """Read any registered input format (SVG, SVGZ, PNG, JPEG, ...), chosen by extension.

        Parameters
        ----------
        path : str or os.PathLike
            The file to read.
        format : str, optional
            Format name or extension. Defaults to None, which follows the
            extension of `path`.
        **options
            Loader options.

        Returns
        -------
        Document
            The loaded document.

        Raises
        ------
        ValueError
            If the options ask for every page (``page=None``); use :meth:`open_all`.

        See Also
        --------
        from_string : Parse SVG text.
        open_all : Every page or slide of a file.

        Examples
        --------
        >>> import tempfile, pathlib
        >>> from svgwriter import Document
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "a.svg"
        ...     Document(10, 10).save(path)
        ...     print(len(Document.open(path)))
        0
        """
        from ..export import load

        result = load(path, format, **options)
        if isinstance(result, list):
            raise ValueError("these options read every page; use Document.open_all for a list of documents")
        return result

    @classmethod
    def open_all(cls, path: AnyPath, *, format: str | None = None, **options: Any) -> list[Document]:
        """Read every page of a PDF, every slide of a PowerPoint deck, or the one drawing of other formats.

        Parameters
        ----------
        path : str or os.PathLike
            The file to read.
        format : str, optional
            Format name or extension. Defaults to None, which follows the
            extension of `path`.
        **options
            Loader options other than the page choice.

        Returns
        -------
        list of Document
            One document per page or slide; a single-page format gives a list of one.

        See Also
        --------
        open : Read one page.
        svgwriter.export.save : Writes a list of documents as pages or slides.

        Examples
        --------
        >>> import tempfile, pathlib
        >>> import svgwriter as svg
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = svg.export.save([svg.Document(10, 10), svg.Document(20, 5)], pathlib.Path(folder) / "a.pdf")
        ...     [page.root.get("width") for page in svg.Document.open_all(path)]
        [10.0, 20.0]
        """
        from ..export import find_importer, load

        page_option = find_importer(format or path).page_option
        if page_option is not None:
            options[page_option] = None
        result = load(path, format, **options)
        return result if isinstance(result, list) else [result]

    async def save_async(self, path: AnyPath, **options: Any) -> None:
        """Write the SVG text to *path* in a worker thread.

        Parameters
        ----------
        path : str or os.PathLike
            Destination file.
        **options
            ``options`` or fields of :class:`~svgwriter.io.SerializeOptions`.

        See Also
        --------
        save : The synchronous version.

        Examples
        --------
        >>> import asyncio, tempfile, pathlib
        >>> from svgwriter import Document
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     path = pathlib.Path(folder) / "a.svg"
        ...     asyncio.run(Document(10, 10).save_async(path))
        ...     print(path.exists())
        True
        """
        from ..io import write_async

        await write_async(self.root, path, **options)

    def render_animation(
        self,
        path: AnyPath,
        fps: float = DEFAULT_FPS,
        duration: float | None = None,
        renderer: Renderer | str | None = None,
        *,
        update: Update | None = None,
        ffmpeg: str | None = None,
    ) -> FilePath:
        """Render frames through *renderer* and encode them with ffmpeg.

        See :func:`svgwriter.video.render_animation` for the parameters.
        ffmpeg is located before any frame is rendered.

        Parameters
        ----------
        path : str or os.PathLike
            Output file; the extension picks the encoder.
        fps : float, optional
            Frames per second. Defaults to 30.0.
        duration : float, optional
            Seconds to render. Defaults to the end of the document's SMIL animations.
        renderer : callable or str, optional
            A renderer, a registered name such as ``"skia"`` or ``"module:function"``.
            Defaults to None, which raises; there is no default renderer.
        update : callable, optional
            ``update(document, seconds)`` called before each frame. Defaults to None.
        ffmpeg : str, optional
            The ffmpeg executable. Defaults to ``ffmpeg`` found on ``PATH``.

        Returns
        -------
        pathlib.Path
            The written file.

        Raises
        ------
        FFmpegNotFoundError
            When ffmpeg is missing.
        FFmpegError
            When ffmpeg fails.

        See Also
        --------
        svgwriter.video.iter_frames : The frames without encoding.

        Examples
        --------

        >>> from svgwriter import Document, Rect
        >>> doc = Document(8, 6)
        >>> doc.render_animation("out.gif", duration=1, renderer="skia")  # doctest: +SKIP
        """
        from ..video.animation import render_animation

        return render_animation(self, path, fps, duration, renderer, update=update, ffmpeg=ffmpeg)
