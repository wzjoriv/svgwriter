"""
SMIL out to PowerPoint: collect each element's animations as slide effects and attach them to its shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._anim_smil import Effect, smil_effect
from ._constants import ANIMATION_KEY, P_NS
from ._pptx_timing import timing_xml

if TYPE_CHECKING:
    from ...document import Document
    from ...elements.core import Element

__all__ = ["SlideAnimations", "slide_animations"]

_ENTRANCES = frozenset({"fade_in", "appear"})
_START_HIDDEN = (("visibility", "hidden"), ("opacity", "0"))


@dataclass
class SlideAnimations:
    """One drawing's effects, keyed to the elements of an animation-free copy that is drawn instead.

    Attributes
    ----------
    document : Document
        The copy to draw: no SMIL elements, every element in its resting state.
    effects : dict of str to list of Effect
        Effects per :data:`ANIMATION_KEY` value.
    dropped : list of str
        Animations PowerPoint cannot play.
    shapes : list of (int, Effect)
        Shape ids and effects gathered while drawing, see :meth:`attach`.
    used : set of str
        Keys that reached at least one shape.
    targets : dict of str to str
        The tag of each animated element, per key.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(20, 20)
    >>> _ = doc.rect(0, 0, 5, 5).animate.spin()
    >>> [e.kind for found in slide_animations(doc).effects.values() for e in found]
    ['rotate']
    """

    document: Document
    effects: dict[str, list[Effect]] = field(default_factory=dict)
    dropped: list[str] = field(default_factory=list)
    shapes: list[tuple[int, Effect]] = field(default_factory=list)
    used: set[str] = field(default_factory=set)
    targets: dict[str, str] = field(default_factory=dict)

    def attach(self, shape: Any, source: Element | None) -> None:
        """Queue the effects of *source* and its ancestors for the drawn *shape*."""
        node = source
        while shape is not None and node is not None:
            key = node.get(ANIMATION_KEY)
            if key is not None:
                self.used.add(str(key))
                self.shapes += [(shape.shape_id, effect) for effect in self.effects.get(str(key), [])]
            node = node.parent

    def write(self, slide: Any, size: tuple[float, float]) -> list[str]:
        """Add the queued effects to *slide*; return the animations that had no shape to play on."""
        from lxml import etree

        missing = [f"animation on <{tag}>" for key, tag in self.targets.items() if key not in self.used]
        if self.shapes:
            root = slide._element
            timing = etree.fromstring(timing_xml(self.shapes, size))
            extension = root.find(f"{{{P_NS}}}extLst")
            if extension is not None:
                extension.addprevious(timing)
            else:
                root.append(timing)
        return self.dropped + missing


def _describe(animation: Element) -> str:
    name = animation.get("attributeName") or animation.get("type") or "path"
    parent = animation.parent
    return f"{animation.tag} {name} on <{parent.tag if parent is not None else '?'}>"


def slide_animations(document: Document) -> SlideAnimations:
    """Read the SMIL of *document* into slide effects and an animation-free copy to draw.

    Parameters
    ----------
    document : Document
        The drawing; it is not modified.

    Returns
    -------
    SlideAnimations
        The copy, the effects keyed to its elements and the dropped animations.

    Examples
    --------
    >>> import svgwriter as svg
    >>> doc = svg.Document(20, 20)
    >>> _ = doc.path("M0 0 L5 5").animate.morph(svg.path("M0 0 L5 0"))
    >>> slide_animations(doc).dropped
    ['animate d on <path>']
    """
    from ..._internal._layers import ancestry
    from ..._internal._rendering import view_matrix
    from ...document import Document
    from ...elements.animation import AnimationElement
    from ...ops.render import page_size

    copy = Document(root=document.root.clone(), theme=document.theme)
    result = SlideAnimations(copy)
    root = copy.root
    with copy._prepared():
        view = view_matrix(copy, *page_size(copy))
    for animation in [e for e in root.iter() if isinstance(e, AnimationElement)]:
        target = animation.parent
        if target is None:
            continue
        effect = None
        if animation.get("href") is None and animation.get("xlink:href") is None:
            effect = smil_effect(animation, view @ ancestry(target, root)[0])
        if effect is None:
            result.dropped.append(_describe(animation))
        elif effect.kind:
            key = str(target.get(ANIMATION_KEY) or len(result.targets))
            target.set(ANIMATION_KEY, key)
            result.targets[key] = target.tag
            result.effects.setdefault(key, []).append(effect)
        target.remove(animation)
    for key, effects in result.effects.items():
        if any(effect.kind in _ENTRANCES for effect in effects):
            target = next(e for e in root.iter() if e.get(ANIMATION_KEY) == key)
            for name, value in _START_HIDDEN:
                if str(target.get(name, "")) == value:
                    target.set(name, None)
    return result
