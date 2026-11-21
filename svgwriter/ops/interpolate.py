"""
Interpolation between numbers, colors, transforms, path data and whole elements (morphing).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, TypeVar

import numpy as np

from ..model.color.color import Color, as_color
from ..model.pathdata.data import PathData
from ..model.transform.matrix import Matrix, Point
from ._constants import DISCRETE_SWITCH, FULL_TURN, GEOMETRY_SKIP, HALF_TURN
from ._morph import blend_outlines

if TYPE_CHECKING:
    from ..model.elements.core import Element

__all__ = ["interpolate", "register_interpolator", "unregister_interpolator"]

T = TypeVar("T")


def interpolate(a: T, b: T, t: float) -> T:
    """The value a fraction *t* of the way from *a* to *b* (``t=0`` gives *a*, ``t=1`` gives *b*).

    Works on numbers, ``(x, y)`` points and numeric sequences, colors (in
    RGBA), :class:`~svgwriter.model.transform.Matrix` (translation, rotation, skew
    and scale separately, so turns stay turns), :class:`~svgwriter.PathData`
    and elements. Two elements of the same kind and shape interpolate their
    attributes; anything else is morphed as outlines: outlines pair with
    outlines and holes with holes (a contour without a partner grows from or
    shrinks to its centre), each pair is resampled to one point count and
    started where the points move least, so in-between shapes do not twist.
    Inside elements, attribute values that cannot be blended (keywords,
    different strings, lists of different lengths) switch at ``t = 0.5``, as
    SMIL's discrete mode does. Other types are added with
    :func:`register_interpolator`.

    Parameters
    ----------
    a, b : object
        Start and end values of the same kind.
    t : float
        Fraction of the way; values outside ``0..1`` extrapolate numbers.

    Returns
    -------
    object
        A new value; neither input is changed.

    Raises
    ------
    TypeError
        If no rule blends *a* with *b* (for example a number and a color).

    See Also
    --------
    svgwriter.Color.mix : Color blending on its own.
    register_interpolator : Teach interpolate a new type.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.interpolate(0, 10, 0.25)
    2.5
    >>> svg.interpolate(svg.Color.parse("red"), svg.Color.parse("blue"), 0.5).hex
    '#800080'
    >>> svg.interpolate(svg.circle(0, 0, 2), svg.circle(10, 0, 4), 0.5).r
    3.0
    >>> morph = svg.interpolate(svg.rect(0, 0, 10, 10), svg.circle(5, 5, 5), 0.5)
    >>> morph.tag
    'path'
    >>> svg.interpolate(1, "bold", 0.5)
    Traceback (most recent call last):
    ...
    TypeError: cannot interpolate int and str; teach it with svg.register_interpolator
    """
    blend = _find(a, b)
    if blend is None:
        raise TypeError(f"cannot interpolate {type(a).__name__} and {type(b).__name__}; "
                        "teach it with svg.register_interpolator")
    return blend(a, b, t)  # type: ignore[no-any-return]


def register_interpolator(kind: type | Callable[[object], bool],
                          blend: Callable[[Any, Any, float], Any]) -> None:
    """Teach :func:`interpolate` to blend values of a new kind.

    Registered rules are tried before the built-in ones, newest first, so a
    rule can also replace how a built-in type blends.

    Parameters
    ----------
    kind : type or callable
        A class (instances and subclasses match) or a predicate
        ``kind(value) -> bool``. A rule applies when both values match.
    blend : callable
        ``blend(a, b, t)`` returning the value a fraction *t* from *a* to *b*.

    See Also
    --------
    unregister_interpolator : Remove the rule again.
    interpolate : Uses the rules.

    Examples
    --------
    >>> import svgwriter as svg
    >>> class Weight(int):
    ...     pass
    >>> svg.register_interpolator(Weight, lambda a, b, t: Weight(round(a + (b - a) * t, -2)))
    >>> svg.interpolate(Weight(400), Weight(700), 0.5)
    600
    >>> svg.unregister_interpolator(Weight)
    """
    _USER_RULES.insert(0, (kind, _predicate(kind), blend))


def unregister_interpolator(kind: type | Callable[[object], bool]) -> None:
    """Remove the rule registered for *kind* with :func:`register_interpolator`.

    Parameters
    ----------
    kind : type or callable
        The class or predicate given when registering.

    Raises
    ------
    KeyError
        If no rule is registered for *kind*.

    Examples
    --------
    >>> import svgwriter as svg
    >>> svg.unregister_interpolator(complex)
    Traceback (most recent call last):
    ...
    KeyError: 'no interpolator registered for complex'
    """
    for index, (registered, _, _) in enumerate(_USER_RULES):
        if registered is kind:
            del _USER_RULES[index]
            return
    raise KeyError(f"no interpolator registered for {getattr(kind, '__name__', kind)}")


def _predicate(kind: type | Callable[[object], bool]) -> Callable[[object], bool]:
    if isinstance(kind, type):
        return lambda value: isinstance(value, kind)
    return kind


def _find(a: object, b: object) -> Callable[[Any, Any, float], Any] | None:
    for _, matches, blend in _USER_RULES:
        if matches(a) and matches(b):
            return blend
    exact = _EXACT.get(type(a))
    if exact is not None and _EXACT.get(type(b)) is exact:
        return exact
    for kind, blend in _RULES:
        if kind(a) and kind(b):
            return blend
    return None


def _attribute(a: object, b: object, t: float) -> Any:
    """Blend two attribute values, switching at ``t = 0.5`` when they do not blend."""
    blend = _find(a, b)
    if blend is None:
        return a if t < DISCRETE_SWITCH else b
    return blend(a, b, t)


def _number(a: float, b: float, t: float) -> float:
    return float(a) + (float(b) - float(a)) * t


def _sequence(a: Any, b: Any, t: float) -> Any:
    if len(a) != len(b):
        return a if t < DISCRETE_SWITCH else b
    values = [interpolate(x, y, t) for x, y in zip(a, b, strict=True)]
    return Point(*values) if isinstance(a, Point) else type(a)(values) if isinstance(a, tuple) else values


def _color(a: Any, b: Any, t: float) -> Color:
    first, second = as_color(a), as_color(b)
    return Color(*(_number(x, y, t) for x, y in zip(first.rgba, second.rgba, strict=True)))


def _angle(a: float, b: float, t: float) -> float:
    turn = (b - a + HALF_TURN) % FULL_TURN - HALF_TURN
    return a + turn * t


def _matrix(a: Matrix, b: Matrix, t: float) -> Matrix:
    (ax, ay, ar, ak, asx, asy), (bx, by, br, bk, bsx, bsy) = a.decompose(), b.decompose()
    return (Matrix.translate(_number(ax, bx, t), _number(ay, by, t)) @ Matrix.rotate(_angle(ar, br, t))
            @ Matrix.skew_x(_number(ak, bk, t)) @ Matrix.scale(_number(asx, bsx, t), _number(asy, bsy, t)))


def _is_color(value: object) -> bool:
    if isinstance(value, Color):
        return True
    if isinstance(value, str):
        try:
            as_color(value)
        except ValueError:
            return False
        return True
    return False


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float, np.floating, np.integer)) and not isinstance(value, bool)


def _is_sequence(value: object) -> bool:
    return isinstance(value, (tuple, list)) and all(_is_number(v) or _is_sequence(v) for v in value)


def _array(a: Any, b: Any, t: float) -> Any:
    first, second = np.asarray(getattr(a, "array", a), dtype=float), np.asarray(getattr(b, "array", b), dtype=float)
    if first.shape != second.shape:
        return a if t < DISCRETE_SWITCH else b
    mixed = first + (second - first) * t
    return type(a)(mixed) if hasattr(a, "array") else mixed


def _is_array(value: object) -> bool:
    return isinstance(value, np.ndarray) or isinstance(getattr(value, "array", None), np.ndarray)


def _is_element(value: object) -> bool:
    from ..model.elements.core import Element

    return isinstance(value, Element)


_RULES: Final[list[tuple[Callable[[object], bool], Callable[[Any, Any, float], Any]]]] = [
    (_is_number, _number),
    (lambda v: isinstance(v, Matrix), _matrix),
    (lambda v: isinstance(v, PathData), blend_outlines),
    (_is_array, _array),
    (_is_element, lambda a, b, t: _elements(a, b, t)),
    (_is_sequence, _sequence),
    (_is_color, _color),
]

_EXACT: Final[dict[type, Callable[[Any, Any, float], Any]]] = {
    int: _number, float: _number, Color: _color, Matrix: _matrix, PathData: blend_outlines,
}

_USER_RULES: Final[list[tuple[type | Callable[[object], bool], Callable[[object], bool],
                              Callable[[Any, Any, float], Any]]]] = []


def _same_shape(a: Element, b: Element) -> bool:
    if type(a) is not type(b) or len(a.children) or len(b.children):
        return False
    for key in set(a.attributes) | set(b.attributes):
        x, y = a.attributes.get(key), b.attributes.get(key)
        if key == "points" and not (_is_array(x) and _is_array(y) and np.shape(x.array) == np.shape(y.array)):  # type: ignore[union-attr]
            return False
        if key == "d" and not (isinstance(x, PathData) and isinstance(y, PathData)):
            return False
    return True


def _elements(a: Element, b: Element, t: float) -> Element:
    if _same_shape(a, b):
        result = a.clone()
        for key in set(a.attributes) | set(b.attributes):
            if key in ("id", "transform"):
                continue
            result.attributes.pop(key, None)
            value = _attribute(a.attributes.get(key), b.attributes.get(key), t)
            if value is not None:
                result.set(key, value)
    else:
        result = _morph(a, b, t)
    if hasattr(a, "t") and hasattr(b, "t"):
        pivot = interpolate(a.anchor, b.anchor, t)  # type: ignore[attr-defined]
        about = Matrix.translate(pivot.x, pivot.y)
        result.t = about @ _matrix(about.inverse() @ a.t @ about, about.inverse() @ b.t @ about, t) @ about.inverse()  # type: ignore[attr-defined]
    return result


def _geometry(element: Element) -> frozenset[str]:
    return getattr(type(element), "geometry_attributes", frozenset())


def _morph(a: Element, b: Element, t: float) -> Element:
    """Both as local outlines, blended; paint and other attributes blend or switch."""
    from ..model.elements.shapes import Path

    data = blend_outlines(a.local_outline(), b.local_outline(), t)  # type: ignore[attr-defined]
    path = Path(data)
    geometry = GEOMETRY_SKIP | _geometry(a) | _geometry(b)
    for key in (set(a.attributes) | set(b.attributes)) - geometry:
        value = _attribute(a.attributes.get(key), b.attributes.get(key), t)
        if value is not None:
            path.set(key, value)
    return path
