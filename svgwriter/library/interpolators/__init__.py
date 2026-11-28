"""
Built-in interpolators: how ``svg.interpolate``, tweens, morphs and batch blends mix numbers, transforms, path
data, arrays, batches, elements, sequences and colours; add your own with ``@svg.preset.interpolator``.

They are tried in that order, after any of your own; the first whose ``kind`` matches both values blends them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal._presets import INTERPOLATORS
from ...model.color.color import Color, as_color
from ...model.pathdata.data import PathData
from ...model.transform.matrix import Matrix, Point
from ...ops._constants import DISCRETE_SWITCH, FULL_TURN, GEOMETRY_SKIP, HALF_TURN
from ...ops._morph import blend_outlines
from ...ops.interpolate import interpolate

if TYPE_CHECKING:
    from ...model.batch import Batch
    from ...model.elements.core import Element

__all__ = ["array", "batch", "color", "element", "matrix", "number", "path", "sequence"]


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float, np.floating, np.integer)) and not isinstance(value, bool)


def _is_sequence(value: object) -> bool:
    return isinstance(value, (tuple, list)) and all(_is_number(v) or _is_sequence(v) for v in value)


def _is_array(value: object) -> bool:
    return isinstance(value, np.ndarray) or isinstance(getattr(value, "array", None), np.ndarray)


def _is_batch(value: object) -> bool:
    from ...model.batch import Batch

    return isinstance(value, Batch)


def _is_element(value: object) -> bool:
    from ...model.elements.core import Element

    return isinstance(value, Element)


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


@INTERPOLATORS(kind=_is_number)
def number(a: float, b: float, t: float) -> float:
    """Numbers along a straight line; *t* outside ``0..1`` extrapolates.

    Parameters
    ----------
    a, b : float
        Start and end.
    t : float
        Fraction of the way.

    Returns
    -------
    float
        ``a + (b - a) * t``.

    Examples
    --------
    >>> from svgwriter.library.interpolators import number
    >>> number(0, 10, 0.25)
    2.5
    """
    return float(a) + (float(b) - float(a)) * t


def _angle(a: float, b: float, t: float) -> float:
    turn = (b - a + HALF_TURN) % FULL_TURN - HALF_TURN
    return a + turn * t


@INTERPOLATORS(kind=Matrix)
def matrix(a: Matrix, b: Matrix, t: float) -> Matrix:
    """Transforms blended as translation, rotation (the short way), skew and scale, so turns stay turns.

    Parameters
    ----------
    a, b : Matrix
        Start and end transforms.
    t : float
        Fraction of the way.

    Returns
    -------
    Matrix
        The blended transform.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.library.interpolators import matrix
    >>> abs(matrix(svg.Matrix.rotate(350), svg.Matrix.rotate(10), 0.5).decompose()[2]) < 1e-9
    True
    """
    (ax, ay, ar, ak, asx, asy), (bx, by, br, bk, bsx, bsy) = a.decompose(), b.decompose()
    return (Matrix.translate(number(ax, bx, t), number(ay, by, t)) @ Matrix.rotate(_angle(ar, br, t))
            @ Matrix.skew_x(number(ak, bk, t)) @ Matrix.scale(number(asx, bsx, t), number(asy, bsy, t)))


@INTERPOLATORS(kind=PathData)
def path(a: PathData, b: PathData, t: float) -> PathData:
    """Path data morphed as outlines: contours paired, resampled to one point count and aligned so they do not twist.

    Parameters
    ----------
    a, b : PathData
        Start and end outlines.
    t : float
        Fraction of the way.

    Returns
    -------
    PathData
        The in-between outline.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.library.interpolators import path
    >>> round(path(svg.rect(0, 0, 10, 10).local_outline(), svg.circle(5, 5, 5).local_outline(), 0.5).bbox.width)
    10
    """
    return blend_outlines(a, b, t)


@INTERPOLATORS(kind=_is_array)
def array(a: Any, b: Any, t: float) -> Any:
    """NumPy arrays (and values holding one as ``.array``, like point lists) element-wise; other shapes switch halfway.

    Parameters
    ----------
    a, b : numpy.ndarray or object with ``array``
        Start and end.
    t : float
        Fraction of the way.

    Returns
    -------
    numpy.ndarray or object
        The blend, of *a*'s type.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.library.interpolators import array
    >>> array(np.zeros(2), np.ones(2), 0.5).tolist()
    [0.5, 0.5]
    """
    first, second = np.asarray(getattr(a, "array", a), dtype=float), np.asarray(getattr(b, "array", b), dtype=float)
    if first.shape != second.shape:
        return a if t < DISCRETE_SWITCH else b
    mixed = first + (second - first) * t
    return type(a)(mixed) if hasattr(a, "array") else mixed


@INTERPOLATORS(kind=_is_batch)
def batch(a: Batch, b: Batch, t: float) -> Batch:
    """Batches of the same size, every item at once; batches of different sizes switch halfway.

    Parameters
    ----------
    a, b : Batch
        Start and end batches.
    t : float
        Fraction of the way.

    Returns
    -------
    Batch
        The blended batch.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.library.interpolators import batch
    >>> batch(svg.batch.circles([0], [0], [2]), svg.batch.circles([0], [0], [4]), 0.5).items[0].r
    3.0
    """
    return a._blend(b, t)


@INTERPOLATORS(kind=_is_element)
def element(a: Element, b: Element, t: float) -> Element:
    """Elements: the same kind and shape blend attribute by attribute, anything else morphs as outlines.

    Attribute values blend with the interpolators (those registered for the attribute first) and switch halfway
    when none applies; the transforms blend about the elements' anchors.

    Parameters
    ----------
    a, b : Element
        Start and end elements.
    t : float
        Fraction of the way.

    Returns
    -------
    Element
        A new element: a copy of *a* blended, or a ``<path>`` for a morph.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter.library.interpolators import element
    >>> element(svg.circle(0, 0, 2), svg.circle(10, 0, 4), 0.5).r
    3.0
    """
    if _same_shape(a, b):
        result = a.clone()
        for key in set(a.attributes) | set(b.attributes):
            if key in ("id", "transform"):
                continue
            result.attributes.pop(key, None)
            value = _attribute(key, a.attributes.get(key), b.attributes.get(key), t)
            if value is not None:
                result.set(key, value)
    else:
        result = _morph(a, b, t)
    if hasattr(a, "matrix") and hasattr(b, "matrix"):
        pivot = interpolate(a.anchor, b.anchor, t)  # type: ignore[attr-defined]
        about = Matrix.translate(pivot.x, pivot.y)
        result.matrix = about @ matrix(about.inverse() @ a.matrix @ about, about.inverse() @ b.matrix @ about, t) @ about.inverse()  # type: ignore[attr-defined]
    return result


@INTERPOLATORS(kind=_is_sequence)
def sequence(a: Any, b: Any, t: float) -> Any:
    """Points and nested numeric tuples or lists item by item; different lengths switch halfway.

    Parameters
    ----------
    a, b : tuple or list
        Start and end.
    t : float
        Fraction of the way.

    Returns
    -------
    tuple or list
        The blend, of *a*'s type.

    Examples
    --------
    >>> from svgwriter.library.interpolators import sequence
    >>> sequence((0, 0), (10, 20), 0.5)
    (5.0, 10.0)
    """
    if len(a) != len(b):
        return a if t < DISCRETE_SWITCH else b
    values = [interpolate(x, y, t) for x, y in zip(a, b, strict=True)]
    return Point(*values) if isinstance(a, Point) else type(a)(values) if isinstance(a, tuple) else values


@INTERPOLATORS(kind=_is_color)
def color(a: Any, b: Any, t: float) -> Color:
    """Colours (or colour strings) channel by channel in RGBA.

    Parameters
    ----------
    a, b : Color or str
        Start and end colours.
    t : float
        Fraction of the way.

    Returns
    -------
    Color
        The blended colour.

    See Also
    --------
    svgwriter.Color.mix : Colour blending on its own.

    Examples
    --------
    >>> from svgwriter.library.interpolators import color
    >>> color("red", "blue", 0.5).hex
    '#800080'
    """
    first, second = as_color(a), as_color(b)
    return Color(*(number(x, y, t) for x, y in zip(first.rgba, second.rgba, strict=True)))


def _attribute(name: str, a: object, b: object, t: float) -> Any:
    """Blend two values of attribute *name*, switching at ``t = 0.5`` when they do not blend."""
    blend = INTERPOLATORS.match(a, b, name)
    if blend is None:
        return a if t < DISCRETE_SWITCH else b
    return blend(a, b, t)


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


def _geometry(item: Element) -> frozenset[str]:
    return getattr(type(item), "geometry_attributes", frozenset())


def _morph(a: Element, b: Element, t: float) -> Element:
    """Both as local outlines, blended; paint and other attributes blend or switch."""
    from ...model.elements.shapes import Path

    data = blend_outlines(a.local_outline(), b.local_outline(), t)  # type: ignore[attr-defined]
    result = Path(data)
    geometry = GEOMETRY_SKIP | _geometry(a) | _geometry(b)
    for key in (set(a.attributes) | set(b.attributes)) - geometry:
        value = _attribute(key, a.attributes.get(key), b.attributes.get(key), t)
        if value is not None:
            result.set(key, value)
    return result


INTERPOLATORS.seal()
