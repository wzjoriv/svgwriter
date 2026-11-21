"""
Where fonts live on each OS, the families tried for CSS generic names, and a summary of what resolves.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ._constants import (
    EMOJI_SAMPLE,
    FONT_DIRS,
    GENERIC_CANDIDATES,
    MAC_FALLBACK_FAMILIES,
    MACOS,
    SUMMARY_FAMILY,
    SUMMARY_GENERICS,
)
from ._system import system

__all__ = ["FontSummary", "fallback_families", "font_dirs", "font_summary", "generic_candidates", "scans_fallback"]

_SUMMARY_GENERICS = ("sans-serif", "serif", "monospace")
_EMOJI = "\U0001F600"


def font_dirs() -> list[Path]:
    """The installed-font folders of this OS that exist.

    Returns
    -------
    list of Path
        System and per-user font folders, in search order.

    Examples
    --------
    >>> from svgwriter._internal._platform import font_dirs
    >>> all(folder.is_dir() for folder in font_dirs())
    True
    """
    folders = (Path(os.path.expanduser(os.path.expandvars(entry))) for entry in FONT_DIRS[system().os])
    return [folder for folder in folders if folder.is_dir()]


def generic_candidates(generic: str) -> tuple[str, ...]:
    """The concrete families tried, in order, for a CSS generic family.

    Parameters
    ----------
    generic : str
        ``"sans-serif"``, ``"serif"``, ``"monospace"``, ``"cursive"`` or ``"fantasy"`` (any case);
        anything else has no candidates.

    Returns
    -------
    tuple of str
        Family names; the first one installed is used.

    Examples
    --------
    >>> from svgwriter._internal._platform import generic_candidates
    >>> "DejaVu Sans" in generic_candidates("Sans-Serif")
    True
    """
    return GENERIC_CANDIDATES.get(generic.lower(), ())


def scans_fallback() -> bool:
    """Whether per-character fallback must scan families itself (macOS, where skia's matcher crashes).

    Returns
    -------
    bool
        True on macOS.

    Examples
    --------
    >>> from svgwriter._internal._platform import scans_fallback
    >>> isinstance(scans_fallback(), bool)
    True
    """
    return system().os == MACOS


def fallback_families() -> tuple[str, ...]:
    """Families searched first for a missing glyph when :func:`scans_fallback` is True.

    Returns
    -------
    tuple of str
        Common macOS families covering CJK, Indic, Arabic, Thai and emoji.

    Examples
    --------
    >>> from svgwriter._internal._platform import fallback_families
    >>> "Apple Color Emoji" in fallback_families()
    True
    """
    return MAC_FALLBACK_FAMILIES


@dataclass(frozen=True)
class FontSummary:
    """The installed fonts and what the generic families resolve to.

    Attributes
    ----------
    families : int
        Number of installed font families.
    resolved : dict of str to str
        ``sans-serif``, ``serif``, ``monospace`` and ``emoji`` to the family that draws them.
    folders : list of str
        The font folders found.

    Examples
    --------
    >>> from svgwriter._internal._platform import font_summary
    >>> font_summary().families > 0
    True
    """

    families: int
    resolved: dict[str, str]
    folders: list[str]

    def to_dict(self) -> dict[str, Any]:
        """The fields as a plain dictionary (for JSON).

        Returns
        -------
        dict of str to Any
            Every attribute by name.

        Examples
        --------
        >>> from svgwriter._internal._platform import font_summary
        >>> sorted(font_summary().to_dict())
        ['families', 'folders', 'resolved']
        """
        return asdict(self)


def font_summary() -> FontSummary:
    """Count the installed families and resolve the generic families and an emoji.

    Returns
    -------
    FontSummary
        The family count, what ``sans-serif``, ``serif``, ``monospace`` and emoji resolve to, and the
        font folders.

    Examples
    --------
    >>> from svgwriter._internal._platform import font_summary
    >>> sorted(font_summary().resolved)
    ['emoji', 'monospace', 'sans-serif', 'serif']
    """
    import skia

    from .._typography._fonts import font_for, resolve_font

    manager = skia.FontMgr.RefDefault()
    resolved = {generic: resolve_font(generic, 1.0, "normal", False).getTypeface().getFamilyName()
                for generic in SUMMARY_GENERICS}
    emoji = font_for(EMOJI_SAMPLE, SUMMARY_FAMILY, 1.0)
    resolved["emoji"] = emoji.getTypeface().getFamilyName() if emoji.unicharToGlyph(ord(EMOJI_SAMPLE)) else ""
    return FontSummary(manager.countFamilies(), resolved, [str(folder) for folder in font_dirs()])
