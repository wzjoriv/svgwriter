"""
Porter-Duff compositing and blend modes on RGBA arrays.

Operators reuse the SVG names: :class:`CompositeOperator` from
``feComposite`` and :class:`BlendMode` from ``feBlend``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Final

import numpy as np

from ..elements.filters import BlendMode, CompositeOperator
from ._constants import ARITHMETIC_TERMS

__all__ = ["Operator", "composite_rgba", "resolve_operator"]

Operator = CompositeOperator | BlendMode | str
Planes = tuple[np.ndarray, np.ndarray]
Rule = Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Sequence[float]], Planes]


def _porter_duff(fa: Callable[[np.ndarray, np.ndarray], np.ndarray],
                 fb: Callable[[np.ndarray, np.ndarray], np.ndarray]) -> Rule:
    def rule(ca: np.ndarray, aa: np.ndarray, cb: np.ndarray, ab: np.ndarray, k: Sequence[float]) -> Planes:
        wa, wb = fa(aa, ab), fb(aa, ab)
        return wa * ca + wb * cb, wa * aa + wb * ab

    return rule


def _blend(mix: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], np.ndarray]) -> Rule:
    def rule(ca: np.ndarray, aa: np.ndarray, cb: np.ndarray, ab: np.ndarray, k: Sequence[float]) -> Planes:
        return mix(ca, aa, cb, ab), 1 - (1 - aa) * (1 - ab)

    return rule


def _arithmetic(ca: np.ndarray, aa: np.ndarray, cb: np.ndarray, ab: np.ndarray, k: Sequence[float]) -> Planes:
    if len(k) != ARITHMETIC_TERMS:
        raise ValueError(f"arithmetic needs k=(k1, k2, k3, k4), got {tuple(k)!r}")
    k1, k2, k3, k4 = (float(v) for v in k)
    alpha = np.clip(k1 * aa * ab + k2 * aa + k3 * ab + k4, 0, 1)
    return np.minimum(np.clip(k1 * ca * cb + k2 * ca + k3 * cb + k4, 0, 1), alpha), alpha


def _over(ca: np.ndarray, aa: np.ndarray, cb: np.ndarray, ab: np.ndarray) -> np.ndarray:
    return ca + (1 - aa) * cb


RULES: Final[dict[Operator, Rule]] = {
    CompositeOperator.OVER: _porter_duff(lambda aa, ab: np.ones_like(aa), lambda aa, ab: 1 - aa),
    CompositeOperator.IN: _porter_duff(lambda aa, ab: ab, lambda aa, ab: np.zeros_like(aa)),
    CompositeOperator.OUT: _porter_duff(lambda aa, ab: 1 - ab, lambda aa, ab: np.zeros_like(aa)),
    CompositeOperator.ATOP: _porter_duff(lambda aa, ab: ab, lambda aa, ab: 1 - aa),
    CompositeOperator.XOR: _porter_duff(lambda aa, ab: 1 - ab, lambda aa, ab: 1 - aa),
    CompositeOperator.ARITHMETIC: _arithmetic,
    BlendMode.NORMAL: _blend(_over),
    BlendMode.MULTIPLY: _blend(lambda ca, aa, cb, ab: (1 - aa) * cb + (1 - ab) * ca + ca * cb),
    BlendMode.SCREEN: _blend(lambda ca, aa, cb, ab: ca + cb - ca * cb),
    BlendMode.DARKEN: _blend(lambda ca, aa, cb, ab: np.minimum(_over(ca, aa, cb, ab), _over(cb, ab, ca, aa))),
    BlendMode.LIGHTEN: _blend(lambda ca, aa, cb, ab: np.maximum(_over(ca, aa, cb, ab), _over(cb, ab, ca, aa))),
}


def resolve_operator(operator: Operator) -> CompositeOperator | BlendMode:
    """Look up a compositing operator by enum member or SVG name.

    Parameters
    ----------
    operator : CompositeOperator, BlendMode or str
        An ``feComposite`` operator (``"over"``, ``"in"``, ``"out"``,
        ``"atop"``, ``"xor"``, ``"arithmetic"``) or an ``feBlend`` mode
        (``"normal"``, ``"multiply"``, ``"screen"``, ``"darken"``, ``"lighten"``).

    Returns
    -------
    CompositeOperator or BlendMode
        The enum member.

    Raises
    ------
    ValueError
        If the name is unknown.

    Examples
    --------
    >>> from svgwriter.ops import resolve_operator
    >>> resolve_operator("multiply")
    <BlendMode.MULTIPLY: 'multiply'>
    """
    if isinstance(operator, (CompositeOperator, BlendMode)):
        return operator
    for kind in (CompositeOperator, BlendMode):
        try:
            return kind(operator)
        except ValueError:
            pass
    names = ", ".join(sorted(str(getattr(key, "value", key)) for key in RULES))
    raise ValueError(f"unknown compositing operator {operator!r}; choose one of {names}")


def composite_rgba(
    source: np.ndarray, backdrop: np.ndarray, operator: Operator = CompositeOperator.OVER,
    *, k: Sequence[float] = (),
) -> np.ndarray:
    """Composite *source* onto *backdrop*.

    Both are straight (unpremultiplied) RGBA in ``0..1`` and broadcast
    against each other, so a ``(1, 1, 4)`` color composites onto a whole image.

    Parameters
    ----------
    source : numpy.ndarray
        ``(..., 4)`` RGBA drawn on top (``A`` in Porter-Duff terms).
    backdrop : numpy.ndarray
        ``(..., 4)`` RGBA underneath (``B``).
    operator : CompositeOperator, BlendMode or str, optional
        How to combine them, as in ``feComposite`` and ``feBlend``. Defaults to ``"over"``.
    k : sequence of float, optional
        ``(k1, k2, k3, k4)`` for ``"arithmetic"``:
        ``k1*A*B + k2*A + k3*B + k4`` on premultiplied values. Defaults to ().

    Returns
    -------
    numpy.ndarray
        ``float32`` straight RGBA with the broadcast shape.

    Raises
    ------
    ValueError
        If the operator is unknown, the shapes do not broadcast, or
        ``arithmetic`` lacks four `k` terms.

    See Also
    --------
    svgwriter.elements.structure.Pixels.composite : Composite the pixels of images.

    Notes
    -----
    The math follows the SVG 1.1 ``feComposite`` and ``feBlend``
    definitions on premultiplied color.

    Examples
    --------
    >>> import numpy as np
    >>> from svgwriter.ops import composite_rgba
    >>> red = np.array([[[1, 0, 0, 0.5]]])
    >>> composite_rgba(red, np.array([[[0, 0, 1, 1]]])).round(2).tolist()
    [[[0.5, 0.0, 0.5, 1.0]]]
    >>> composite_rgba(red, np.zeros((2, 2, 4)), "in").shape
    (2, 2, 4)
    """
    rule = RULES[resolve_operator(operator)]
    a = np.asarray(source, dtype=np.float32)
    b = np.asarray(backdrop, dtype=np.float32)
    aa, ab = a[..., 3:], b[..., 3:]
    color, alpha = rule(a[..., :3] * aa, aa, b[..., :3] * ab, ab, k)
    alpha = np.clip(alpha, 0, 1)
    straight = np.divide(color, alpha, out=np.zeros(np.broadcast_shapes(color.shape, alpha.shape), np.float32),
                         where=alpha > 0)
    return np.concatenate([np.clip(straight, 0, 1), np.broadcast_to(alpha, straight.shape[:-1] + (1,))],
                          axis=-1).astype(np.float32)
