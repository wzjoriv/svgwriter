"""
Preset registries, one per kind: animations and behaviors (``element.animate``), shapes, sizes, patterns,
filters, gradients, markers and effects.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Concatenate, Final, TypeAlias, TypeVar, overload

from ._constants import MOTION_HELPERS
from ._registry import Registry
from ._roles import with_role
from ._typing import P

if TYPE_CHECKING:
    from .._document.sizes import PageSize
    from ..model.attributes.length import LengthLike
    from ..model.elements import Motion
    from ..model.elements.core import Element
    from ..model.elements.text import Character, CharacterRange

__all__ = [
    "ANIMATIONS",
    "BEHAVIORS",
    "EFFECTS",
    "FILTERS",
    "GRADIENTS",
    "KINDS",
    "MARKERS",
    "PATTERNS",
    "SHAPES",
    "SIZES",
    "AnimationPresets",
    "BehaviorPresets",
    "DefinitionPresets",
    "EffectPresets",
    "ShapePresets",
    "SizePresets",
    "catalogue",
]

F = TypeVar("F", bound=Callable[..., Any])
E = TypeVar("E", bound="Element")
Target: TypeAlias = "Element | CharacterRange | Character"
Styler: TypeAlias = Callable[Concatenate["Element", P], object]
Effect: TypeAlias = Callable[Concatenate[Target, P], "Element"]

_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _check_motion(kind: str, other: Registry[Any], name: str, function: Callable[..., object],
                  leading: int, shape: str) -> None:
    """Raise unless *name* is usable on ``element.animate`` and *function* takes *leading* positionals, then options."""
    if not name.isidentifier() or name.startswith("_") or name in MOTION_HELPERS:
        raise ValueError(f"{kind} names are Python identifiers, without a leading underscore and other than "
                         f"{', '.join(sorted(MOTION_HELPERS))}; not {name!r}")
    if other.find(name, plugins=False) is not None:
        clash = ("is a behavior; animations and behaviors" if other.kind == "behavior"
                 else "is an animation preset; behaviors and animations")
        raise ValueError(f"{name!r} {clash} share element.animate, so pick another name")
    parameters = list(inspect.signature(function).parameters.values())
    if len(parameters) < leading or any(parameter.kind not in _POSITIONAL for parameter in parameters[:leading]):
        lead = "the Motion as its first positional parameter" if leading == 1 else \
            "the element and the time in seconds as its first two positional parameters"
        raise TypeError(f"{kind} {name!r} takes {lead}: {shape.format(name=name)}")
    for parameter in parameters[leading:]:
        keyword = parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is not inspect.Parameter.empty
        if not keyword and parameter.kind is not inspect.Parameter.VAR_KEYWORD:
            raise TypeError(f"{kind} {name!r}: option {parameter.name!r} must be keyword-only with a default: "
                            f"{shape.format(name=name)}")


class AnimationPresets(Registry[Callable[..., "Motion | None"]]):
    """Animation presets: a typed function becomes ``element.animate.<name>(...)``.

    Decorate ``function(motion, *, option=default, ...) -> Motion``: the first positional parameter is the
    element's :class:`~svgwriter.Motion`, every option is keyword-only with a default, and it returns the motion
    for chaining (None is accepted). The function stays an ordinary typed function, so
    :meth:`Motion.apply <svgwriter.Motion.apply>` calls it with full completion; the name works wherever
    presets are looked up (``element.animate.bob(...)``, :meth:`Motion.stagger <svgwriter.Motion.stagger>`).
    Use bare, or with ``name=`` and ``replace=``; a replaced built-in stays reachable as a class attribute
    (``svg.Motion.spin(motion, ...)``), so a replacement can wrap it.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.animation
    ... def bob(motion: svg.Motion, *, height: float = 8, dur: float = 1, begin: float = 0) -> svg.Motion:
    ...     return motion.move_by(0, -height, dur / 2, begin=begin).move_by(0, height, dur / 2, begin=begin + dur / 2)
    >>> dot = svg.circle(10, 10, 4)
    >>> _ = dot.animate.apply(bob, height=4).fade_out(begin=1)
    >>> _ = dot.animate.bob(begin=2)
    >>> [child.tag for child in dot.children]
    ['animateTransform', 'animateTransform', 'animate', 'animateTransform', 'animateTransform']
    >>> svg.preset.animation(bob)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: animation 'bob' is already registered by ...bob; pass replace=True to replace it
    >>> _ = svg.preset.animation.unregister("bob")
    """

    @overload
    def register(self, item: F, /, *, name: str | None = None, replace: bool = False) -> F: ...

    @overload
    def register(self, *, name: str | None = None, replace: bool = False) -> Callable[[F], F]: ...

    def register(self, item: F | None = None, /, *, name: str | None = None,
                 replace: bool = False) -> F | Callable[[F], F]:
        return super().register(item, name=name, replace=replace)  # type: ignore[arg-type,return-value]

    __call__ = register

    def prepare(self, name: str, item: Callable[..., Motion | None]) -> Callable[..., Motion | None]:
        _check_motion(self.kind, BEHAVIORS, name, item, 1,
                      "def {name}(motion: svg.Motion, *, option: float = 1.0) -> svg.Motion")
        return item


class BehaviorPresets(Registry[Callable[..., None]]):
    """Behaviors: Python motion that a :class:`~svgwriter.Scene` runs before every frame.

    Decorate ``function(element, seconds, *, option=default, ...) -> None``. Attach it with
    :meth:`Scene.attach <svgwriter.Scene.attach>` or ``element.animate.<name>(...)`` once the element is in a
    scene's document. Saving the scene as SVG or PowerPoint bakes the motion into keyframes. Use bare, or with
    ``name=`` and ``replace=``.

    Examples
    --------
    >>> import math
    >>> import svgwriter as svg
    >>> @svg.preset.behavior
    ... def sway(element: svg.Element, seconds: float, *, angle: float = 10, period: float = 2) -> None:
    ...     element.matrix = element.home.matrix
    ...     element.rotate(angle * math.sin(2 * math.pi * seconds / period))
    >>> class Flag(svg.Scene):
    ...     width, height, duration = 40, 40, 2.0
    ...     def build(self, doc):
    ...         doc.rect(15, 5, 10, 30).animate.sway(angle=20)
    >>> Flag().render(0.5)[:4]
    b'\\x89PNG'
    >>> _ = svg.preset.behavior.unregister("sway")
    """

    @overload
    def register(self, item: F, /, *, name: str | None = None, replace: bool = False) -> F: ...

    @overload
    def register(self, *, name: str | None = None, replace: bool = False) -> Callable[[F], F]: ...

    def register(self, item: F | None = None, /, *, name: str | None = None,
                 replace: bool = False) -> F | Callable[[F], F]:
        return super().register(item, name=name, replace=replace)  # type: ignore[arg-type,return-value]

    __call__ = register

    def prepare(self, name: str, item: Callable[..., None]) -> Callable[..., None]:
        _check_motion(self.kind, ANIMATIONS, name, item, 2,
                      "def {name}(element: svg.Element, seconds: float, *, option: float = 1.0) -> None")
        return item


class ShapePresets(Registry[Callable[..., "Element"]]):
    """Shape presets: a function returning an element, listed by ``svgwriter shapes``.

    The registered wrapper checks the return type, so plugins fail loudly, and marks the element with a theme
    role (``role=``, default ``"shape"``; None leaves it unthemed); presentation keywords the caller passes
    move into the inline style so they keep priority over the role. Use bare, or with ``name=``, ``role=``
    and ``replace=``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.shape
    ... def disc(cx, cy, r, **kwargs):
    ...     return svg.Circle(cx, cy, r, **kwargs)
    >>> str(disc(0, 0, 2, stroke="red"))
    '<circle cx="0" cy="0" r="2" style="stroke:red" class="role-shape"/>'
    >>> svg.preset.shape(name="star")(disc)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: shape 'star' is already registered by svgwriter.catalog.paths._shapes.star (built in); pass replace=True ...
    >>> _ = svg.preset.shape.unregister("disc")
    """

    @overload
    def register(self, item: Callable[P, E], /, *, name: str | None = None, role: str | None = "shape",
                 replace: bool = False) -> Callable[P, E]: ...

    @overload
    def register(self, *, name: str | None = None, role: str | None = "shape",
                 replace: bool = False) -> Callable[[Callable[P, E]], Callable[P, E]]: ...

    def register(self, item: Callable[P, E] | None = None, /, *, name: str | None = None,
                 role: str | None = "shape", replace: bool = False) -> Any:
        def decorate(function: Callable[P, E]) -> Callable[P, E]:
            from ..model.elements.core import Element

            label = name or self.name_of(function)

            @functools.wraps(function)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> E:
                result = function(*args, **kwargs)
                if not isinstance(result, Element):
                    raise TypeError(f"shape {label!r} returned {type(result).__name__}")
                return with_role(result, role, kwargs)

            return self.add(label, wrapper, replace=replace)  # type: ignore[return-value]

        return decorate if item is None else decorate(item)

    __call__ = register


class DefinitionPresets(Registry[Callable[..., "Element"]]):
    """Pattern, filter, gradient or marker presets: functions building a reusable definition.

    Each registered function joins its catalogue (``svg.patterns``, ``svg.filters``, ``svg.gradients``,
    ``svg.markers``) behind a wrapper that checks it returns the right element: a
    :class:`~svgwriter.Pattern`; a :class:`~svgwriter.Filter`; a :class:`~svgwriter.LinearGradient`,
    :class:`~svgwriter.RadialGradient` or a pattern of blends; a :class:`~svgwriter.Marker`. Use bare, or with
    ``name=`` and ``replace=``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.pattern
    ... def bricks(size: float = 8, color: str = "firebrick") -> svg.Pattern:
    ...     return svg.Pattern(svg.rect(0, 0, size, size / 2, fill=color), width=size, height=size,
    ...                        pattern_units="userSpaceOnUse")
    >>> svg.patterns.bricks(4).tag
    'pattern'
    >>> @svg.preset.filter(name="soften")
    ... def blur(amount: float = 1.5) -> svg.Filter:
    ...     return svg.Filter(svg.FeGaussianBlur(amount))
    >>> svg.filters.soften().children[0].tag
    'feGaussianBlur'
    >>> _ = svg.preset.pattern.unregister("bricks"), svg.preset.filter.unregister("soften")
    """

    def __init__(self, kind: str, types: Callable[[], tuple[type, ...]]) -> None:
        super().__init__(kind)
        self._types = types

    @overload
    def register(self, item: Callable[P, E], /, *, name: str | None = None,
                 replace: bool = False) -> Callable[P, E]: ...

    @overload
    def register(self, *, name: str | None = None,
                 replace: bool = False) -> Callable[[Callable[P, E]], Callable[P, E]]: ...

    def register(self, item: Callable[P, E] | None = None, /, *, name: str | None = None,
                 replace: bool = False) -> Any:
        return super().register(item, name=name, replace=replace)  # type: ignore[arg-type]

    __call__ = register

    def prepare(self, name: str, item: Callable[..., Element]) -> Callable[..., Element]:
        kind, types = self.kind, self._types

        @functools.wraps(item)
        def wrapper(*args: Any, **kwargs: Any) -> Element:
            result = item(*args, **kwargs)
            expected = types()
            if not isinstance(result, expected):
                names = " or ".join(cls.__name__ for cls in expected)
                raise TypeError(f"{kind} {name!r} returned {type(result).__name__}, not {names}")
            return result

        return wrapper


class EffectPresets(Registry[Callable[..., "Element"]]):
    """Effects: a function styling an element becomes an effect for any element and for ranges of a text.

    Decorate ``function(element, *, option=default, ...)``, which sets the paint, filter and animations of the
    element in place; a text stays text. The registered effect also takes a range of a text (``text[4:9]``): its
    characters move to a copy placed just above, where only they show, and the function styles that copy, so
    filters reach exactly those characters. Effects answer as ``svg.effects.<name>(target)``,
    ``element.effect(name)`` and ``text[a:b].effect(name)``. Use bare, or with ``name=`` and ``replace=``; an
    effect that only suits some elements raises TypeError for the others.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.effect
    ... def ink(element: svg.Element, *, color: str = "navy") -> None:
    ...     element.fill = color
    >>> doc = svg.Document(200, 40)
    >>> str(doc.text("Hello world", x=0, y=30).effect("ink"))
    '<text x="0" y="30" fill="navy">Hello world</text>'
    >>> str(doc.circle(5, 5, 4).effect("ink", color="red"))
    '<circle cx="5" cy="5" r="4" fill="red"/>'
    >>> layer = ink(doc.text("Hello world", x=0, y=30)[6:11], color="red")
    >>> layer.get("fill"), layer.children[0].get("visibility")
    ('red', 'hidden')
    >>> _ = svg.preset.effect.unregister("ink")
    """

    @overload
    def register(self, item: Styler[P], /, *, name: str | None = None, replace: bool = False) -> Effect[P]: ...

    @overload
    def register(self, *, name: str | None = None,
                 replace: bool = False) -> Callable[[Styler[P]], Effect[P]]: ...

    def register(self, item: Styler[P] | None = None, /, *, name: str | None = None,
                 replace: bool = False) -> Any:
        return super().register(item, name=name, replace=replace)  # type: ignore[arg-type]

    __call__ = register

    def prepare(self, name: str, item: Callable[..., Any]) -> Callable[..., Element]:
        @functools.wraps(item)
        def effect(target: Target, /, *args: Any, **kwargs: Any) -> Element:
            from ..model.elements.core import Element

            if isinstance(target, Element):
                element = target
            elif hasattr(target, "isolate"):
                element = target.isolate()
            else:
                raise TypeError(f"effects apply to an element or a range of a text (text[a:b]), "
                                f"not {type(target).__name__}")
            item(element, *args, **kwargs)
            if element.classes:
                element.to_css()
            return element

        return effect


class SizePresets(Registry["PageSize"]):
    """Named canvas sizes for ``Document(size=name)``, ``Scene.size`` and project files.

    Register with a call, ``svg.preset.size(name, width, height, replace=False)``. Sizes with a physical unit
    (``"210mm"``, ``svg.inch(11)``) make documents whose ``viewBox`` counts in that unit; plain numbers are
    pixels. Every name also works with ``-landscape`` and ``-portrait`` appended, and appears as an attribute
    of :data:`svgwriter.size` with the name turned into an identifier.

    Examples
    --------
    >>> import svgwriter as svg
    >>> _ = svg.preset.size("poster-50x70", "50cm", "70cm")
    >>> svg.size.poster_50x70.landscape.width
    70.0
    >>> svg.Document(size="poster-50x70-landscape").root.get("viewBox").width
    70.0
    >>> _ = svg.preset.size.unregister("poster-50x70")
    """

    def __call__(self, name: str, width: LengthLike, height: LengthLike, *, replace: bool = False) -> PageSize:
        """Register the size *width* by *height* as *name*; a taken name raises ValueError naming its owner."""
        from .._document.sizes import PageSize

        return self.register(PageSize.of(width, height), name=name, replace=replace)

    def name_of(self, item: object) -> str:
        raise TypeError("sizes register with a name: svg.preset.size(name, width, height)")


def _types(*names: str) -> Callable[[], tuple[type, ...]]:
    def types() -> tuple[type, ...]:
        from ..model import elements

        return tuple(getattr(elements, name) for name in names)

    return types


def catalogue(registry: Registry[Any], module: str) -> tuple[Callable[[str], Any], Callable[[], list[str]]]:
    """``__getattr__`` and ``__dir__`` for a catalogue module answering with *registry*'s presets by name.

    Looking presets up at access time keeps replacements (``replace=True``) and user presets visible.
    """

    def lookup(name: str) -> Any:
        found = None if name.startswith("__") else registry.find(name)
        if found is None:
            hint = registry.unknown(name) if not name.startswith("__") else ""
            raise AttributeError(f"module {module!r} has no attribute {name!r}" + (f" ({hint})" if hint else ""))
        return found

    def names() -> list[str]:
        return sorted(registry.list())

    return lookup, names


ANIMATIONS: Final = AnimationPresets("animation")
BEHAVIORS: Final = BehaviorPresets("behavior")
SHAPES: Final = ShapePresets("shape")
SIZES: Final = SizePresets("size")
PATTERNS: Final = DefinitionPresets("pattern", _types("Pattern"))
FILTERS: Final = DefinitionPresets("filter", _types("Filter"))
GRADIENTS: Final = DefinitionPresets("gradient", _types("LinearGradient", "RadialGradient", "Pattern"))
MARKERS: Final = DefinitionPresets("marker", _types("Marker"))
EFFECTS: Final = EffectPresets("effect")
KINDS: Final[dict[str, Registry[Any]]] = {
    "animation": ANIMATIONS, "behavior": BEHAVIORS, "shape": SHAPES, "size": SIZES, "pattern": PATTERNS,
    "filter": FILTERS, "gradient": GRADIENTS, "marker": MARKERS, "effect": EFFECTS}
