"""
Interpolation between numbers, colors, transforms, path data and whole elements (morphing), through the
interpolator registry (``svg.preset.interpolator``).
"""

from __future__ import annotations

from typing import TypeVar

from .._internal._presets import INTERPOLATORS

__all__ = ["interpolate"]

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
    Two batches (:mod:`svgwriter.batch <svgwriter.model.batch>`) of the same
    size blend every item at once.
    Inside elements, attribute values that cannot be blended (keywords,
    different strings, lists of different lengths) switch at ``t = 0.5``, as
    SMIL's discrete mode does. Each kind of value blends with an
    interpolator; add or replace them with ``@svg.preset.interpolator``.

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
    svgwriter.library.interpolators : The built-in interpolators.

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
    TypeError: cannot interpolate int and str; teach it with @svg.preset.interpolator
    """
    blend = INTERPOLATORS.match(a, b)
    if blend is None:
        raise TypeError(f"cannot interpolate {type(a).__name__} and {type(b).__name__}; "
                        "teach it with @svg.preset.interpolator")
    return blend(a, b, t)  # type: ignore[no-any-return]
