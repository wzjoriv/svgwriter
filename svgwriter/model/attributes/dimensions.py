"""
Checking that a value's dimension (length, angle, number) fits the attribute it is set on.
"""

from __future__ import annotations

from ..units.quantities import Quantity
from ._constants import ANGLE_ATTRIBUTES, LENGTH_ATTRIBUTES, PLAIN_VALUE_TYPES

__all__ = ["check_dimension"]


def check_dimension(name: str, value: object) -> None:
    """Refuse a value whose dimension does not fit the attribute *name*.

    Lengths may not go where SVG wants an angle and angles not where it wants a
    length; a `Quantity` (an area, a length per angle, ...) fits no attribute.

    Parameters
    ----------
    name : str
        The SVG attribute name.
    value : object
        The value about to be stored.

    Raises
    ------
    TypeError
        If the dimension does not fit, naming the attribute and the dimension.

    Examples
    --------
    >>> import svgwriter as svg
    >>> check_dimension("width", svg.mm(3) * svg.mm(2))
    Traceback (most recent call last):
    ...
    TypeError: width needs a length, got length²
    """
    if type(value) in PLAIN_VALUE_TYPES:
        return
    from ..units.angles import Angle
    from ..units.lengths import Length

    wants = "an angle" if name in ANGLE_ATTRIBUTES else "a length" if name in LENGTH_ATTRIBUTES else "a number"
    if isinstance(value, Quantity):
        raise TypeError(f"{name} needs {wants}, got {value.dimension}")
    if isinstance(value, Angle) and name in LENGTH_ATTRIBUTES:
        raise TypeError(f"{name} needs a length, got angle")
    if isinstance(value, Length) and name in ANGLE_ATTRIBUTES:
        raise TypeError(f"{name} needs an angle, got length")
