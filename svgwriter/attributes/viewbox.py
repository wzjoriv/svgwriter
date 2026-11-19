"""``viewBox`` and ``preserveAspectRatio``."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Final, NamedTuple

from .._internal._constants import DEFAULT_PRECISION
from .._internal._numbers import format_number

__all__ = ["Align", "MeetOrSlice", "PreserveAspectRatio", "ViewBox"]

_SEPARATORS: Final = re.compile(r"[\s,]+")


class ViewBox(NamedTuple):
    """The ``viewBox`` rectangle in user units.

    A named tuple, so it unpacks as ``min_x, min_y, width, height``.

    Parameters
    ----------
    min_x, min_y : float
        Top-left corner of the visible region.
    width, height : float
        Size of the visible region.

    See Also
    --------
    PreserveAspectRatio : How the box is fitted into the viewport.

    Examples
    --------
    >>> from svgwriter.attributes import ViewBox
    >>> ViewBox(0, 0, 100, 50).svg_value()
    '0 0 100 50'
    """

    min_x: float
    min_y: float
    width: float
    height: float

    @classmethod
    def parse(cls, text: str) -> ViewBox:
        """Parse ``viewBox`` text.

        Parameters
        ----------
        text : str
            Four numbers separated by spaces and/or commas.

        Returns
        -------
        ViewBox
            The parsed box.

        Raises
        ------
        ValueError
            If there are not four numbers, or the width or height is negative.

        Examples
        --------
        >>> from svgwriter.attributes import ViewBox
        >>> ViewBox.parse("0,0 100 50")
        ViewBox(min_x=0.0, min_y=0.0, width=100.0, height=50.0)
        """
        parts = [p for p in _SEPARATORS.split(text.strip()) if p]
        if len(parts) != 4:
            raise ValueError(f"viewBox needs four numbers: {text!r}")
        box = cls(*(float(p) for p in parts))
        if box.width < 0 or box.height < 0:
            raise ValueError("viewBox width and height must be non-negative")
        return box

    @property
    def aspect_ratio(self) -> float:
        """Width divided by height; 0 when the height is zero.

        Examples
        --------
        >>> from svgwriter.attributes import ViewBox
        >>> ViewBox(0, 0, 100, 50).aspect_ratio
        2.0
        """
        return self.width / self.height if self.height else 0.0

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize as attribute text.

        Parameters
        ----------
        precision : int, optional
            Maximum number of decimal places. Defaults to the library default precision.

        Returns
        -------
        str
            The four numbers separated by spaces.

        Examples
        --------
        >>> from svgwriter.attributes import ViewBox
        >>> ViewBox(0, 0, 100.5, 50).svg_value()
        '0 0 100.5 50'
        """
        return " ".join(format_number(v, precision) for v in self)


class Align(str, enum.Enum):
    """Alignment values of ``preserveAspectRatio``.

    ``CENTER`` is an alias of ``X_MID_Y_MID``, the default.

    See Also
    --------
    PreserveAspectRatio : Combines an alignment with meet or slice.

    Examples
    --------
    >>> from svgwriter.attributes import Align
    >>> Align.X_MIN_Y_MAX.value
    'xMinYMax'
    """

    NONE = "none"
    X_MIN_Y_MIN = "xMinYMin"
    X_MID_Y_MIN = "xMidYMin"
    X_MAX_Y_MIN = "xMaxYMin"
    X_MIN_Y_MID = "xMinYMid"
    X_MID_Y_MID = "xMidYMid"
    X_MAX_Y_MID = "xMaxYMid"
    X_MIN_Y_MAX = "xMinYMax"
    X_MID_Y_MAX = "xMidYMax"
    X_MAX_Y_MAX = "xMaxYMax"
    CENTER = "xMidYMid"


class MeetOrSlice(str, enum.Enum):
    """Whether the viewBox is scaled to fit entirely or to cover the viewport.

    See Also
    --------
    PreserveAspectRatio : Uses this setting.

    Examples
    --------
    >>> from svgwriter.attributes import MeetOrSlice
    >>> MeetOrSlice.SLICE.value
    'slice'
    """

    MEET = "meet"
    SLICE = "slice"


@dataclass(frozen=True)
class PreserveAspectRatio:
    """How a viewBox is fitted into its viewport.

    Parameters
    ----------
    align : Align, optional
        Which point of the viewBox lines up with the viewport. Defaults to ``Align.X_MID_Y_MID``.
    meet_or_slice : MeetOrSlice, optional
        Scale to fit entirely (meet) or to cover (slice). Defaults to ``MeetOrSlice.MEET``.
    defer : bool, optional
        Emit the ``defer`` keyword (only meaningful on ``image``). Defaults to False.

    See Also
    --------
    ViewBox : The rectangle being fitted.

    Examples
    --------
    >>> from svgwriter.attributes import Align, MeetOrSlice, PreserveAspectRatio
    >>> str(PreserveAspectRatio(Align.X_MIN_Y_MIN, MeetOrSlice.SLICE))
    'xMinYMin slice'
    """

    align: Align = Align.X_MID_Y_MID
    meet_or_slice: MeetOrSlice = MeetOrSlice.MEET
    defer: bool = False

    @classmethod
    def parse(cls, text: str) -> PreserveAspectRatio:
        """Parse ``preserveAspectRatio`` text.

        Parameters
        ----------
        text : str
            Text such as ``"defer xMinYMax slice"``.

        Returns
        -------
        PreserveAspectRatio
            The parsed value.

        Raises
        ------
        ValueError
            If the text is empty, too long, or contains an unknown keyword.

        Examples
        --------
        >>> from svgwriter.attributes import PreserveAspectRatio
        >>> str(PreserveAspectRatio.parse("none"))
        'none'
        """
        words = text.split()
        defer = bool(words) and words[0] == "defer"
        if defer:
            words = words[1:]
        if not words or len(words) > 2:
            raise ValueError(f"invalid preserveAspectRatio: {text!r}")
        mode = MeetOrSlice(words[1]) if len(words) == 2 else MeetOrSlice.MEET
        return cls(Align(words[0]), mode, defer)

    def svg_value(self, precision: int = DEFAULT_PRECISION) -> str:
        """Serialize as attribute text.

        Parameters
        ----------
        precision : int, optional
            Unused; accepted for a uniform interface. Defaults to the library default precision.

        Returns
        -------
        str
            The keywords; ``meet`` is omitted because it is the default.

        Examples
        --------
        >>> from svgwriter.attributes import PreserveAspectRatio
        >>> PreserveAspectRatio().svg_value()
        'xMidYMid'
        """
        words = ["defer"] if self.defer else []
        words.append(self.align.value)
        if self.meet_or_slice is not MeetOrSlice.MEET:
            words.append(self.meet_or_slice.value)
        return " ".join(words)

    def __str__(self) -> str:
        return self.svg_value()
