"""
Scenes: one animation per class, several per file.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from .._internal._typing import AnyPath
from ._constants import SCENE_FORMAT, SCENE_HEIGHT, SCENE_RENDERER, SCENE_WIDTH
from .animation import DEFAULT_FPS, Renderer, iter_frames, render_animation
from .frames import Frame

if TYPE_CHECKING:
    from ..color.color import ColorLike
    from ..document import Document

__all__ = ["Scene"]


class Scene:
    """An animation: a drawing built once, then changed over time.

    Subclass it, set the class attributes and override :meth:`build` and,
    for procedural motion, :meth:`update`. SMIL animations in the drawing
    play as well. One file can hold several scenes; ``svgwriter animate``
    renders each one.

    Parameters
    ----------
    document : Document, optional
        A finished drawing to animate as it is, instead of calling
        :meth:`build`. Defaults to None.
    name : str, optional
        The scene's name, used for output files. Defaults to the class name.

    Attributes
    ----------
    width, height : float
        Size of the document handed to :meth:`build`. Default 640 by 360.
    fps : float
        Frames per second. Default 30.0.
    duration : float or None
        Seconds to render. Default None, the end of the SMIL animations.
    renderer : callable or str
        ``renderer(document, seconds)``, a registered name or
        ``"module:function"``. Default ``"skia"``.

    See Also
    --------
    svgwriter.video.load_scenes : Collect the scenes of a file or module.
    svgwriter.video.render_animation : The encoder underneath :meth:`save`.

    Notes
    -----
    :meth:`build` receives an empty document of the class's size rather than
    returning one, so ``width`` and ``height`` mean one thing and the method
    holds only drawing code. Keep the elements that :meth:`update` changes on
    ``self``. :meth:`update` receives absolute time, so frames can be rendered
    in any order and a scene can be saved more than once.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Grow(svg.Scene):
    ...     width, height, fps, duration = 40, 40, 4, 1.0
    ...     def build(self, doc):
    ...         self.dot = doc.circle(20, 20, 4, fill="tomato")
    ...     def update(self, seconds):
    ...         self.dot.r = 4 + 12 * seconds
    >>> scene = Grow()
    >>> [frame.index for frame in scene.frames()]
    [0, 1, 2, 3]
    >>> scene.render(0.5)[:4]
    b'\\x89PNG'
    >>> scene.save("grow.gif")  # doctest: +SKIP
    """

    width: ClassVar[float] = SCENE_WIDTH
    height: ClassVar[float] = SCENE_HEIGHT
    fps: ClassVar[float] = DEFAULT_FPS
    duration: ClassVar[float | None] = None
    renderer: ClassVar[Renderer | str] = SCENE_RENDERER

    def __init__(self, document: Document | None = None, *, name: str | None = None) -> None:
        self._document = document
        self.name = name or type(self).__name__

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name!r} {self.width:g}x{self.height:g} at {self.fps:g} fps>"

    def build(self, doc: Document) -> None:
        """Draw the scene into *doc*; called once, on first use of :attr:`document`.

        Parameters
        ----------
        doc : Document
            An empty document of size ``width`` by ``height``.

        See Also
        --------
        update : Change the drawing for each frame.

        Examples
        --------
        >>> import svgwriter as svg
        >>> class Card(svg.Scene):
        ...     width, height = 80, 40
        ...     def build(self, doc):
        ...         doc.rect(0, 0, 80, 40, fill="navy")
        >>> len(Card().document)
        1
        """

    def update(self, seconds: float) -> None:
        """Set the drawing to its state at *seconds*; called before every frame.

        Parameters
        ----------
        seconds : float
            Time since the start of the scene.

        See Also
        --------
        build : Draw the scene once.

        Examples
        --------
        >>> import svgwriter as svg
        >>> class Slide(svg.Scene):
        ...     def build(self, doc):
        ...         self.box = doc.rect(0, 0, 10, 10)
        ...     def update(self, seconds):
        ...         self.box.x = 100 * seconds
        >>> scene = Slide()
        >>> _ = scene.document
        >>> scene.update(0.5)
        >>> scene.box.x
        50.0
        """

    @property
    def document(self) -> Document:
        """The drawing, built on first access.

        Returns
        -------
        Document
            The document passed in, or a new one filled by :meth:`build`.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Scene().document.root.get("viewBox").width
        640.0
        """
        if self._document is None:
            from ..document import Document

            self._document = Document(self.width, self.height)
            self.build(self._document)
        return self._document

    def _advance(self, document: Document, seconds: float) -> None:
        self.update(seconds)

    def frames(self, *, fps: float | None = None, duration: float | None = None,
               renderer: Renderer | str | None = None) -> Iterator[Frame]:
        """Render the frames without encoding them.

        Parameters
        ----------
        fps : float, optional
            Overrides the class's ``fps``.
        duration : float, optional
            Overrides the class's ``duration``.
        renderer : callable or str, optional
            Overrides the class's ``renderer``.

        Yields
        ------
        Frame
            One frame per ``1 / fps`` seconds.

        Raises
        ------
        ValueError
            If no duration is set and the drawing has no SMIL animation.

        See Also
        --------
        save : Encode the frames into a file.

        Examples
        --------
        >>> import svgwriter as svg
        >>> class Blank(svg.Scene):
        ...     width, height, duration = 8, 6, 1.0
        >>> [(f.width, f.height) for f in Blank().frames(fps=2)]
        [(8, 6), (8, 6)]
        """
        return iter_frames(self.document, fps or self.fps, duration or self.duration,
                           renderer or self.renderer, update=self._advance)

    def render(self, seconds: float = 0.0, *, scale: float = 1.0, background: ColorLike | None = None) -> bytes:
        """One frame at *seconds* as PNG bytes, with SMIL applied.

        Parameters
        ----------
        seconds : float, optional
            The moment to draw. Defaults to 0.0.
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
        svgwriter.Document.at : The still copy that is drawn.

        Examples
        --------
        >>> import svgwriter as svg
        >>> svg.Scene(svg.Document(4, 4)).render(scale=2)[:4]
        b'\\x89PNG'
        """
        from ..ops.render import render_png

        document = self.document
        self.update(seconds)
        return render_png(document.at(seconds), scale=scale, background=background)

    def save(self, path: AnyPath | None = None, *, fps: float | None = None, duration: float | None = None,
             renderer: Renderer | str | None = None, ffmpeg: str | None = None) -> Path:
        """Render the scene and encode it with ffmpeg.

        Parameters
        ----------
        path : str or path-like, optional
            Output file; the extension picks the format (``.mp4``, ``.gif``,
            ``.webm``, ``.mov``, ``.apng``; ``.png`` writes numbered frames).
            Defaults to ``<name>.mp4`` in the current folder.
        fps : float, optional
            Overrides the class's ``fps``.
        duration : float, optional
            Overrides the class's ``duration``.
        renderer : callable or str, optional
            Overrides the class's ``renderer``.
        ffmpeg : str, optional
            The ffmpeg executable. Defaults to ``ffmpeg`` on ``PATH``.

        Returns
        -------
        pathlib.Path
            The written file, or the pattern of the numbered frames.

        Raises
        ------
        FFmpegNotFoundError
            Before rendering anything, when ffmpeg is missing.
        FFmpegError
            When ffmpeg fails.

        See Also
        --------
        frames : The frames without encoding.

        Examples
        --------
        >>> import svgwriter as svg
        >>> class Still(svg.Scene):
        ...     width, height, duration = 8, 6, 1.0
        >>> Still().save("still.png", ffmpeg="no-such-ffmpeg")
        Traceback (most recent call last):
        ...
        svgwriter.video._ffmpeg.FFmpegNotFoundError: ...
        """
        target = Path(path) if path is not None else Path(f"{self.name}.{SCENE_FORMAT}")
        return render_animation(self.document, target, fps or self.fps, duration or self.duration,
                                renderer or self.renderer, update=self._advance, ffmpeg=ffmpeg)

    def _repr_svg_(self) -> str:
        return self.document._repr_svg_()

    def _repr_html_(self) -> str:
        return self.document._repr_html_()
