"""
Python motion in a scene: attaching behaviors, running them each frame, and baking everything into SMIL.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Concatenate, TypeVar

from .._internal._typing import P
from ._bake import bake_document, bake_times
from ._constants import BAKE_TOLERANCE
from .animation import animation_duration

if TYPE_CHECKING:
    from ..document import Document
    from ..model.elements.core import Element

__all__ = ["SceneMotion"]

E = TypeVar("E", bound="Element")


class SceneMotion:
    """Behaviors and baking, mixed into :class:`~svgwriter.Scene`."""

    fps: float
    duration: float | None
    _behaviors: list[tuple[Element, Callable[..., None], tuple[Any, ...], dict[str, Any]]]

    if TYPE_CHECKING:
        @property
        def document(self) -> Document: ...

        def update(self, seconds: float) -> None: ...

    def attach(self, element: E, behavior: Callable[Concatenate[E, float, P], None], *args: P.args,
               **kwargs: P.kwargs) -> E:
        """Run *behavior* on *element* before every frame: ``behavior(element, seconds, *args, **kwargs)``.

        Typed with the behavior's own options, so editors complete and check them. Behaviors run in the
        order they were attached, all before :meth:`update`. The first one attached to an element records
        its :attr:`~svgwriter.Element.home`. ``element.animate.<name>(...)`` does the same for a behavior
        registered with :func:`@svg.preset.behavior <svgwriter.catalog.preset.behavior>`.

        Parameters
        ----------
        element : Element
            What the behavior moves; usually already in :attr:`document`.
        behavior : callable
            ``behavior(element, seconds, *, option=default, ...)``; it need not be registered.
        *args, **kwargs
            Passed on to *behavior* after the element and the time.

        Returns
        -------
        Element
            *element*, so it can be kept in one line: ``self.bell = self.attach(doc.rect(...), wiggle)``.

        See Also
        --------
        bake : The behaviors as SMIL.

        Examples
        --------
        >>> import svgwriter as svg
        >>> def slide(element: svg.Element, seconds: float, *, speed: float = 10) -> None:
        ...     element.t = element.home.t
        ...     element.translate(speed * seconds)
        >>> class Train(svg.Scene):
        ...     width, height, duration = 60, 20, 2.0
        ...     def build(self, doc):
        ...         self.car = self.attach(doc.rect(0, 5, 10, 10), slide, speed=20)
        >>> scene = Train()
        >>> scene.render(1.0)[:4]
        b'\\x89PNG'
        >>> scene.car.t.e
        20.0
        """
        if "_home" not in element.__dict__:
            element.__dict__["_home"] = element.clone()
        self._behaviors.append((element, behavior, args, kwargs))
        return element

    def _advance(self, document: Document, seconds: float) -> None:
        for element, behavior, args, kwargs in self._behaviors:
            behavior(element, seconds, *args, **kwargs)
        self.update(seconds)

    def _moves(self) -> bool:
        """Whether Python changes the drawing over time (behaviors or an overridden update)."""
        from .scene import Scene

        return bool(self._behaviors) or type(self).update is not Scene.update

    def bake(self, fps: float | None = None, *, duration: float | None = None,
             tolerance: float = BAKE_TOLERANCE) -> Document:
        """A copy of the document whose SMIL plays what the behaviors and :meth:`update` do.

        The scene is sampled ``fps`` times a second. Each element's changes become ``<animate>``,
        ``<animateTransform>`` and ``<set>`` children with as few keyframes as keep every sample within
        *tolerance*: numbers and colours interpolate (a path's ``d`` while its commands keep their shape),
        transforms split into translate, rotate, skew and scale, and other values switch with ``<set>``.
        Changing text becomes one copy per text shown in turn, and elements added or removed are shown or
        hidden with ``visibility``. The document's own SMIL is kept and plays on top, as in the video.
        Anything SMIL cannot express is left out and listed in one warning.

        Parameters
        ----------
        fps : float, optional
            Samples per second. Defaults to the scene's ``fps``.
        duration : float, optional
            Seconds to sample. Defaults to the scene's ``duration``, else the end of its SMIL.
        tolerance : float, optional
            Largest difference allowed between the baked animation and a sample, in user units, degrees,
            scale factors or colour channels (``0..1``). Defaults to 0.01.

        Returns
        -------
        Document
            The baked copy; the scene's own document keeps its Python state.

        Raises
        ------
        ValueError
            If no duration is set and the drawing has no SMIL animation.

        See Also
        --------
        save : Uses this for ``.svg``, ``.svgz``, ``.html`` and ``.pptx``.

        Notes
        -----
        Baking runs the behaviors and :meth:`update` for every sample, so it leaves the scene at its last
        moment. What is not expressed: an element moved to another parent, changes of an id, CSS
        declarations that are not SVG properties, an attribute removed with no initial value to return to,
        and transforms squashed flat with a skew.

        Examples
        --------
        >>> import svgwriter as svg
        >>> class Slide(svg.Scene):
        ...     width, height, fps, duration = 100, 20, 10, 1.0
        ...     def build(self, doc):
        ...         self.box = doc.rect(0, 5, 10, 10, fill="red")
        ...     def update(self, seconds):
        ...         self.box.x = 90 * seconds
        >>> baked = Slide().bake()
        >>> animation = baked[0].children[0]
        >>> animation.tag, animation.get("values"), animation.get("keyTimes")
        ('animate', '0;90', '0;1')
        >>> baked.at(0.5)[0].get("x")
        '45'
        """
        from ..document import Document

        length = duration or self.duration or animation_duration(self.document)
        if length is None:
            raise ValueError("pass duration=...; the scene has none and its drawing has no SMIL animation")
        if not self._moves():
            root = self.document.root.clone()
            return Document(root=root, theme=self.document.theme)  # type: ignore[arg-type]
        baked, issues = bake_document(self.document, self._advance, bake_times(fps or self.fps, length), tolerance)
        if issues:
            warnings.warn(f"SMIL cannot express these changes, left out of the baked animation: "
                          f"{'; '.join(dict.fromkeys(issues))}", stacklevel=2)
        return baked
