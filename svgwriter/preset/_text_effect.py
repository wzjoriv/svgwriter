"""
``@svg.preset.text_effect``: a function styling a ``<text>`` becomes an effect for whole texts and ranges.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Concatenate, TypeAlias, overload

from .._internal._presets import TEXT_EFFECTS
from .._internal._typing import P

if TYPE_CHECKING:
    from ..elements import Character, CharacterRange, Text

__all__ = ["text_effect"]

Target: TypeAlias = "Text | CharacterRange | Character"
Styler: TypeAlias = Callable[Concatenate["Text", P], object]
Effect: TypeAlias = Callable[Concatenate[Target, P], "Text"]


def _text_of(target: Target) -> Text:
    """The element an effect styles: the text itself, or a layer showing only the range's characters."""
    from ..elements import Text

    if isinstance(target, Text):
        return target
    isolate = getattr(target, "isolate", None)
    if isolate is None:
        raise TypeError(f"text effects apply to a Text or a range of one (text[a:b]), not {type(target).__name__}")
    return isolate()


def _keep_over_roles(text: Text) -> None:
    """Move the paint an effect set into the inline style when *text* has classes, such as theme roles.

    Class rules in CSS win over presentation attributes, so a role's fill would otherwise hide the effect's.
    """
    if text.classes:
        text.to_css()


@overload
def text_effect(function: Styler[P], /, *, name: str | None = None, replace: bool = False) -> Effect[P]: ...


@overload
def text_effect(*, name: str | None = None, replace: bool = False) -> Callable[[Styler[P]], Effect[P]]: ...


def text_effect(function: Styler[P] | None = None, /, *, name: str | None = None,
                replace: bool = False) -> Effect[P] | Callable[[Styler[P]], Effect[P]]:
    """Register a function that styles a ``<text>`` as a text effect.

    The function receives a whole :class:`~svgwriter.Text` and sets its paint, filter and animations;
    the text stays text. The registered effect also takes a range (``text[4:9]``): the range's characters
    move to a copy of the text placed just above it, where only they show, and the function styles that
    copy, so filters reach exactly those characters. Effects answer as ``svg.text_effects.<name>(target)``,
    ``text.effect(name)`` and ``text[a:b].effect(name)``.

    Parameters
    ----------
    function : callable, optional
        ``function(text, *, option=default, ...)``, styling *text* in place. Given when used as a bare
        decorator.
    name : str, optional
        The effect name. Defaults to None, which takes the function's name.
    replace : bool, optional
        Replace an effect already registered under the name, a built-in one included. Defaults to False.

    Returns
    -------
    callable
        ``effect(target, *, option=default, ...) -> Text``, returning the styled element, or a decorator
        that registers the function and returns that effect.

    Raises
    ------
    ValueError
        If the name is taken and `replace` is False; the message names the owner.

    See Also
    --------
    svgwriter.text_effects : The built-in effects.
    svgwriter.CharacterRange.isolate : The copy a range effect styles.

    Examples
    --------
    >>> import svgwriter as svg
    >>> @svg.preset.text_effect
    ... def ink(text: svg.Text, *, color: str = "navy") -> None:
    ...     text.fill = color
    >>> doc = svg.Document(200, 40)
    >>> line = doc.text("Hello world", x=0, y=30)
    >>> str(line.effect("ink"))
    '<text x="0" y="30" fill="navy">Hello world</text>'
    >>> layer = ink(doc.text("Hello world", x=0, y=30)[6:11], color="red")
    >>> layer.get("fill"), layer.children[0].get("visibility")
    ('red', 'hidden')
    >>> svg.preset.unregister("text_effect", "ink")
    """

    def decorate(func: Styler[P]) -> Effect[P]:
        label = name or func.__name__

        @functools.wraps(func)
        def effect(target: Target, /, *args: P.args, **kwargs: P.kwargs) -> Text:
            text = _text_of(target)
            func(text, *args, **kwargs)
            _keep_over_roles(text)
            return text

        TEXT_EFFECTS.add(label, effect, replace=replace)
        return effect

    return decorate if function is None else decorate(function)
