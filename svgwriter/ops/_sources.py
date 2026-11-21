"""
Loading faces: font sources (paths, bytes, streams, ``data:`` URIs), collections and installed families.
"""

from __future__ import annotations

import base64
import difflib
import os
import urllib.parse
from functools import cache
from pathlib import Path
from typing import Any, BinaryIO, TypeAlias

import skia

from .._internal._constants import GENERIC_CANDIDATES
from .._internal._font_constants import BASE64_MARKER, DATA_URI, REGULAR_SUBFAMILY, SUGGESTIONS
from .._internal._font_match import describe
from .._internal._font_names import face_count, family_names
from ._faces import Face

__all__ = ["FontSource", "family_of", "installed_faces", "load", "load_face"]

FontSource: TypeAlias = str | os.PathLike[str] | bytes | BinaryIO
"""A font file path, its contents (bytes or a binary stream) or a ``data:`` URI."""


def _read(source: FontSource) -> tuple[Path | None, bytes]:
    """The path (None for contents) and bytes of a font source; ``data:`` URIs are decoded, never fetched."""
    if isinstance(source, bytes):
        return None, source
    if hasattr(source, "read"):
        return None, source.read()
    if isinstance(source, str) and source.startswith(DATA_URI):
        header, _, payload = source.partition(",")
        if header.endswith(BASE64_MARKER):
            return None, base64.b64decode(payload)
        return None, urllib.parse.unquote_to_bytes(payload)
    path = Path(os.fspath(source))
    return path, path.read_bytes()


def load(source: FontSource) -> list[tuple[Any, Path | None, bytes]]:
    """Every face (skia typeface, path, bytes) of a font file or its contents; collections give several."""
    path, blob = _read(source)
    data = skia.Data.MakeWithCopy(blob)
    typefaces = [skia.Typeface.MakeFromData(data, index) for index in range(face_count(blob))]
    if not typefaces or None in typefaces:
        raise ValueError(f"cannot read a font from {str(path) if path else 'the data'!r}")
    return [(typeface, path, blob) for typeface in typefaces]


def load_face(name: str, typeface: Any, override: tuple[float, str] | None = None, path: Path | None = None,
          blob: bytes | None = None) -> Face:
    """A face with descriptors read from its tables (OS/2, axes and the subfamily name) unless overridden."""
    subfamily = family_names(typeface)[1]
    weight, style = override if override is not None else (None, None)
    return Face.of(name, typeface, describe(typeface, weight, style, subfamily=subfamily), path, blob, subfamily)


def family_of(source: FontSource) -> str:
    """The family of a file's first face, typographic name first."""
    return family_names(load(source)[0][0])[0]


@cache
@cache
def _installed_families() -> tuple[str, ...]:
    """Every installed family name, indexed once on first need."""
    manager = skia.FontMgr.RefDefault()
    return tuple(manager.getFamilyName(index) for index in range(manager.countFamilies()))


def installed_faces(name: str) -> tuple[str, list[Face]]:
    """The concrete family and its installed faces; generic names pick the first installed candidate.

    The font manager names each style, so no font tables are read here.
    """
    manager = skia.FontMgr.RefDefault()
    for family in (*GENERIC_CANDIDATES.get(name.lower(), ()), name):
        styles = manager.matchFamily(family)
        if styles.count():
            faces = []
            for index in range(styles.count()):
                typeface, subfamily = styles.createTypeface(index), styles.getStyle(index)[1] or REGULAR_SUBFAMILY
                faces.append(Face.of(family, typeface, describe(typeface, subfamily=subfamily), subfamily=subfamily))
            return family, faces
    families = {family.lower(): family for family in _installed_families()}
    close = [families[match] for match in difflib.get_close_matches(name.lower(), families, n=SUGGESTIONS)]
    hint = f"; did you mean {' or '.join(repr(match) for match in close)}?" if close else ""
    raise LookupError(f"no installed font family {name!r}{hint} (load files with Typeface.from_files)")
