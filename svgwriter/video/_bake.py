"""
Baking: sample a scene's Python motion and write it into a copy of its document as SMIL.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast

from .._internal._constants import ANIMATED_DEFAULTS, EPSILON
from ..attributes.cascade import INHERITED
from ..attributes.style import Style
from ..elements.animation import Animate, AnimateTransform, AnimationElement, Set
from ._bake_record import Record, Tape, label
from ._bake_series import Vector, colors, fill, number, numbers, parts, runs, simplify, template
from ._constants import BAKE_DISCRETE, BAKE_HIDDEN, BAKE_INITIAL, BAKE_PARTS, BAKE_VISIBILITY, BAKE_VISIBLE

if TYPE_CHECKING:
    from ..document import Document
    from ..elements.core import Element
    from ..transform.matrix import Matrix

__all__ = ["bake_document", "bake_times"]


def bake_times(fps: float, duration: float) -> list[float]:
    """Sample times from 0 to *duration* inclusive, at least *fps* per second, evenly spaced."""
    count = max(1, math.ceil(duration * fps - EPSILON))
    return [duration * index / count for index in range(count + 1)]


def _hex(rgb: Vector) -> str:
    from ..color.color import Color

    return Color(*(min(max(channel, 0.0), 1.0) for channel in rgb)).hex


def _seconds(value: float) -> str:
    return f"{number(value)}s"


class _Baker:
    """Turns the recorded series of one element at a time into SMIL children of its baked copy."""

    def __init__(self, tape: Tape, times: Sequence[float], tolerance: float) -> None:
        self.tape, self.times, self.tolerance = tape, times, tolerance
        self.issues: list[str] = []

    def keyframes(self, first: int, last: int, vectors: Sequence[Vector], render: Callable[[Vector], str]
                  ) -> dict[str, Any]:
        times = self.times[first:last + 1]
        keep = simplify(times, vectors, self.tolerance)
        span = times[-1] - times[0]
        return {"values": ";".join(render(vectors[k]) for k in keep),
                "key_times": ";".join(number((times[k] - times[0]) / span) for k in keep),
                "begin": _seconds(times[0]), "dur": _seconds(span), "fill": "freeze"}

    def discrete(self, name: str, values: Sequence[str], conflict: bool) -> list[Element]:
        """Sets at each change; one discrete ``<animate>`` from 0 s when other SMIL drives the same attribute."""
        changes = [index for index in range(1, len(values)) if values[index] != values[index - 1]]
        if not conflict:
            return [Set(attribute_name=name, to=values[index], begin=_seconds(self.times[index]), fill="freeze")
                    for index in changes]
        keys = [0, *changes]
        return [Animate(attribute_name=name, values=";".join(values[k] for k in keys), calc_mode="discrete",
                        key_times=";".join(number(self.times[k] / self.times[-1]) for k in keys),
                        dur=_seconds(self.times[-1]), fill="freeze")]

    def attribute(self, name: str, values: Sequence[str], conflict: bool) -> list[Element]:
        if name in BAKE_DISCRETE:
            return self.discrete(name, values, conflict)
        rgb = colors(values)
        if rgb is not None:
            return [Animate(attribute_name=name, **self.keyframes(0, len(values) - 1, rgb, _hex))]
        spans = runs(values)
        if conflict and len(spans) > 1:
            return self.discrete(name, values, conflict)
        made: list[Element] = []
        for first, last in spans:
            vectors = [numbers(value) for value in values[first:last + 1]]
            if vectors[0] and len(set(values[first:last + 1])) > 1:
                made.append(Animate(attribute_name=name, **self.keyframes(
                    first, last, vectors, functools.partial(fill, template(values[first])))))
            elif first > 0:
                made.append(Set(attribute_name=name, to=values[first], begin=_seconds(self.times[first]),
                                fill="freeze"))
        return made

    def transform(self, element: Element, target: Element, matrices: Sequence[Matrix]) -> list[Element]:
        """Animations of ``translate``, then ``rotate``, ``skewX`` and ``scale`` about the element's centre.

        Relative to the first transform when it is invertible (all additive), else replacing it.
        """
        base = matrices[0]
        if all(matrix.isclose(base, self.tolerance) for matrix in matrices):
            return []
        relative = abs(base.determinant) > EPSILON
        box = target.local_bbox()  # type: ignore[attr-defined]
        pivot = (box.x + box.width / 2, box.y + box.height / 2) if box is not None else (0.0, 0.0)
        series, singular = parts([base.inverse() @ matrix for matrix in matrices] if relative else matrices,
                                 pivot)
        if singular:
            self.issues.append(f"{label(target)} transform collapsing to a line at "
                               f"{number(self.times[singular[0]])} s")
        attribute = type(element).transform_attribute  # type: ignore[attr-defined]

        def make(kind: str, vectors: Sequence[Vector], additive: str | None = "sum") -> Element:
            return AnimateTransform(kind, attribute_name=attribute, additive=additive, **self.keyframes(
                0, len(vectors) - 1, vectors, lambda vector: " ".join(map(number, vector))))

        moving = {kind: any(abs(a - b) > self.tolerance for vector in series[kind]
                            for a, b in zip(vector, identity, strict=True)) for kind, identity in BAKE_PARTS}
        made = [make("translate", series["translate"], "sum" if relative else None)
                ] if moving["translate"] or not relative else []
        turns = [make(kind, series[kind]) for kind, _ in BAKE_PARTS[1:] if moving[kind]]
        if turns and any(pivot):
            count = len(self.times)
            turns = [make("translate", [pivot] * count), *turns, make("translate", [(-pivot[0], -pivot[1])] * count)]
        return made + turns

    def values(self, held: Sequence[Record], name: str) -> list[str] | None:
        """The value of *name* at every frame; a missing one is inherited or the initial value."""
        found = []
        for index, record in enumerate(held):
            value = record.values.get(name)
            if value is None and name in INHERITED:
                value = self.tape.inherited(index, record.parent, name)
            value = value if value is not None else ANIMATED_DEFAULTS.get(name, BAKE_INITIAL.get(name))
            if value is None:
                return None
            found.append(value)
        return found

    def visibility(self, held: Sequence[Record], present: Sequence[bool], shown: Sequence[bool]) -> list[str]:
        result = []
        for index, record in enumerate(held):
            own = record.values.get(BAKE_VISIBILITY) or self.tape.inherited(index, record.parent, BAKE_VISIBILITY)
            result.append((own or BAKE_VISIBLE) if present[index] and shown[index] else BAKE_HIDDEN)
        return result

    def bake(self, key: int) -> None:
        tape, element = self.tape, self.tape.elements[key]
        target = tape.baked[key]
        held, present = tape.series(key)
        conflicts = {str(child.get("attributeName")) for child in target.children
                     if isinstance(child, AnimationElement)}
        names = sorted({name for record in held for name in record.values} - {BAKE_VISIBILITY})
        made: list[Element] = []
        for name in names:
            values = self.values(held, name)
            if values is None:
                self.issues.append(f"{label(target)} {name} removed")
            elif len(set(values)) > 1 and name == "id":
                self.issues.append(f"{label(target)} id changed")
            elif len(set(values)) > 1:
                made += self.attribute(name, values, name in conflicts)
                _unstyle(target, name, values[0])
        if held[0].matrix is not None:
            made += self.transform(element, target, [record.matrix for record in held])  # type: ignore[misc]
        if len({record.loose for record in held}) > 1:
            self.issues.append(f"{label(target)} CSS declarations other than SVG properties")
        if len({record.parent for record, shown in zip(held, present, strict=True) if shown}) > 1:
            self.issues.append(f"{label(target)} moved to another parent")
        for index, animation in enumerate(made):
            target.insert(index, animation)
        self.show(target, held, present, BAKE_VISIBILITY in conflicts)

    def show(self, target: Element, held: Sequence[Record], present: Sequence[bool],
             conflict: bool) -> None:
        """Visibility sets for presence and text changes (one copy per text), else own visibility changes."""
        texts = list(dict.fromkeys(record.text for record in held))
        own = any(BAKE_VISIBILITY in record.values for record in held)
        parent = held[0].parent
        follows = parent is not None and present == [parent in frame for frame in self.tape.frames]
        if len(texts) == 1 and (all(present) or (follows and not own)):
            values = self.values(held, BAKE_VISIBILITY) if own else None
            if values is not None and len(set(values)) > 1:
                _unstyle(target, BAKE_VISIBILITY, values[0])
                _prepend(target, self.discrete(BAKE_VISIBILITY, values, conflict))
            return
        copies = [target]
        for text in texts[1:]:
            copy = target.clone()
            copy.id = None
            _retext(copy, text)
            owner = cast("Element", target.parent)
            owner.insert(next(i for i, child in enumerate(owner.children) if child is copies[-1]) + 1, copy)
            copies.append(copy)
        if len(texts) > 1:
            _retext(target, texts[0])
        for copy, text in zip(copies, texts, strict=True):
            values = self.visibility(held, present, [record.text == text for record in held])
            if values[0] == BAKE_HIDDEN:
                _unstyle(copy, BAKE_VISIBILITY, BAKE_HIDDEN)
                copy.set(BAKE_VISIBILITY, BAKE_HIDDEN)
            _prepend(copy, self.discrete(BAKE_VISIBILITY, values, conflict))


def _prepend(target: Element, animations: list[Element]) -> None:
    for index, animation in enumerate(animations):
        target.insert(index, animation)


def _unstyle(target: Element, name: str, value: str) -> None:
    """Move property *name* from the inline style to an attribute, which SMIL then animates."""
    style = target.get("style")
    if style is None:
        return
    declarations = Style(str(style))
    if name not in declarations:
        return
    del declarations[name]
    target.set("style", declarations if declarations else None)
    target.set(name, value)


def _retext(target: Element, text: tuple[str, ...]) -> None:
    strings = iter(text)
    target.children = [next(strings, "") if isinstance(child, str) else child for child in target.children]
    target.children += list(strings)


def bake_document(document: Document, advance: Callable[[Document, float], None], times: Sequence[float],
                  tolerance: float) -> tuple[Document, list[str]]:
    """A copy of *document* whose SMIL replays what *advance* does at *times*, and what SMIL cannot express."""
    from ..document import Document

    tape = Tape(document)
    for time in times:
        advance(document, time)
        tape.capture()
    tape.place()
    baker = _Baker(tape, times, tolerance)
    for key in list(tape.elements):
        baker.bake(key)
    root = cast("Element", tape.root)
    root.__dict__["_source_path"] = document.root.__dict__.get("_source_path")
    return Document(root=root, theme=document.theme), baker.issues  # type: ignore[arg-type]
