"""
Grid tracks: parsing ``"auto"``, fixed and ``"1fr"`` sizes, sizing them like CSS grid, and auto-placement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias

from ..units.lengths import Length
from ._constants import AUTO, FR, IMPLICIT_TRACK
from ._lengths import resolve

__all__ = ["Track", "TrackLike", "TracksLike", "auto_place", "parse_tracks", "size_tracks"]

TrackLike: TypeAlias = float | str | Length
TracksLike: TypeAlias = int | str | Sequence[TrackLike]


@dataclass(frozen=True)
class Track:
    """One grid row or column.

    Attributes
    ----------
    fixed : float or None
        The size in user units for a fixed track.
    flex : float
        The share of a flexible (``fr``) track; 0 for fixed and ``auto`` tracks.

    Examples
    --------
    >>> from svgwriter.model.layout._tracks import Track
    >>> Track(None, 2.0).flex
    2.0
    """

    fixed: float | None = None
    flex: float = 0.0


def _track(value: TrackLike, scale: float) -> Track:
    if isinstance(value, str):
        text = value.strip()
        if text == AUTO:
            return Track()
        if text.endswith(FR):
            flex = float(text[: -len(FR)])
            if flex <= 0:
                raise ValueError(f"a flexible track needs a positive share, got {value!r}")
            return Track(None, flex)
    return Track(resolve(value, scale))


def parse_tracks(spec: TracksLike | None, scale: float = 1.0) -> list[Track]:
    """Tracks from a count, a CSS-like string (``"auto 1fr 40"``) or a sequence of sizes.

    Parameters
    ----------
    spec : int, str, sequence or None
        A count of ``"1fr"`` tracks, space-separated sizes, or one size per track: ``"auto"``
        (fits the largest child), a length (fixed) or ``"Nfr"`` (a share of the free space).
        None gives no explicit tracks.
    scale : float, optional
        User units per CSS pixel for lengths with units. Defaults to 1.0.

    Returns
    -------
    list of Track
        The tracks in order.

    Raises
    ------
    ValueError
        For a count below one or an unreadable size.

    Examples
    --------
    >>> from svgwriter.model.layout._tracks import parse_tracks
    >>> parse_tracks("auto 2fr 40")
    [Track(fixed=None, flex=0.0), Track(fixed=None, flex=2.0), Track(fixed=40.0, flex=0.0)]
    >>> len(parse_tracks(3))
    3
    """
    if spec is None:
        return []
    if isinstance(spec, int) and not isinstance(spec, bool):
        if spec < 1:
            raise ValueError(f"a grid needs at least one track, got {spec}")
        return [_track(IMPLICIT_TRACK, scale)] * spec
    parts = spec.split() if isinstance(spec, str) else list(spec)
    return [_track(part, scale) for part in parts]


def auto_place(spans: Sequence[tuple[int, int]], columns: int) -> list[tuple[int, int]]:
    """Cells for items in order, row by row, each taking ``(column span, row span)`` free cells.

    Parameters
    ----------
    spans : sequence of (int, int)
        Each item's column and row span; column spans are capped at `columns`.
    columns : int
        Number of columns.

    Returns
    -------
    list of (int, int)
        Each item's first ``(column, row)``.

    Examples
    --------
    >>> from svgwriter.model.layout._tracks import auto_place
    >>> auto_place([(1, 1), (2, 1), (1, 2), (1, 1)], 3)
    [(0, 0), (1, 0), (0, 1), (1, 1)]
    """
    taken: set[tuple[int, int]] = set()
    cells: list[tuple[int, int]] = []
    column = row = 0
    for wide, tall in spans:
        wide = min(wide, columns)
        while True:
            if column + wide > columns:
                column, row = 0, row + 1
                continue
            cover = {(c, r) for c in range(column, column + wide) for r in range(row, row + tall)}
            if not cover & taken:
                break
            column += 1
        taken |= cover
        cells.append((column, row))
        column += wide
    return cells


def size_tracks(tracks: Sequence[Track], contents: Sequence[float], spanning: Sequence[tuple[int, int, float]],
                available: float | None, gap: float) -> list[float]:
    """Track sizes: fixed as given, ``auto`` to content, ``fr`` sharing what is left.

    Parameters
    ----------
    tracks : sequence of Track
        The tracks.
    contents : sequence of float
        Largest size of the single-track children in each track.
    spanning : sequence of (int, int, float)
        ``(first track, count, size)`` for children spanning several tracks; the shortfall is
        spread over the non-fixed tracks they cover.
    available : float or None
        Space for the tracks and gaps, or None to size flexible tracks to their content.
    gap : float
        Space between tracks.

    Returns
    -------
    list of float
        One size per track.

    Notes
    -----
    A flexible track never gets less than its content, as CSS ``1fr`` means ``minmax(auto, 1fr)``.
    Without an available size every ``1fr`` takes the largest content per share, so ``1fr``
    tracks come out equal.

    Examples
    --------
    >>> from svgwriter.model.layout._tracks import parse_tracks, size_tracks
    >>> size_tracks(parse_tracks("40 auto 1fr"), [0, 12, 5], [], 100, 4)
    [40.0, 12.0, 40.0]
    >>> size_tracks(parse_tracks(2), [10, 30], [], None, 0)
    [30.0, 30.0]
    """
    sizes = [track.fixed if track.fixed is not None else float(content)
             for track, content in zip(tracks, contents, strict=True)]
    for first, count, size in spanning:
        covered = range(first, first + count)
        growable = [index for index in covered if tracks[index].fixed is None]
        shortfall = size - sum(sizes[index] for index in covered) - gap * (count - 1)
        for index in growable if shortfall > 0 else ():
            sizes[index] += shortfall / len(growable)
    flexible = {index for index, track in enumerate(tracks) if track.flex}
    if not flexible:
        return sizes
    if available is None:
        unit = max(sizes[index] / tracks[index].flex for index in flexible)
    else:
        rest = available - gap * (len(tracks) - 1) - sum(size for i, size in enumerate(sizes) if i not in flexible)
        while True:
            unit = max(rest, 0.0) / sum(tracks[index].flex for index in flexible)
            bigger = {index for index in flexible if sizes[index] > unit * tracks[index].flex}
            if not bigger:
                break
            flexible -= bigger
            rest -= sum(sizes[index] for index in bigger)
            if not flexible:
                return sizes
    for index in flexible:
        sizes[index] = unit * tracks[index].flex
    return sizes
