"""
Loading faces: font sources (paths, bytes, streams, ``data:`` URIs), collections and installed families.
"""

from __future__ import annotations

import base64
import difflib
import os
import urllib.parse
import warnings
from functools import cache
from pathlib import Path
from typing import Any, BinaryIO, TypeAlias

import skia

from ..._internal._platform import generic_candidates
from ..._internal._typography._font_constants import BASE64_MARKER, DATA_URI, REGULAR_SUBFAMILY, SUGGESTIONS
from ..._internal._typography._font_match import describe
from ..._internal._typography._font_names import face_count, family_names
from ..._internal._typography._sfnt import collection_member
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


def _typeface(data: Any, blob: bytes, index: int) -> Any:
    """Face *index* of a font; a collection member some font managers cannot open is opened as its own file."""
    typeface = skia.Typeface.MakeFromData(data, index)
    if typeface is None and face_count(blob) > 1:
        typeface = skia.Typeface.MakeFromData(skia.Data.MakeWithCopy(collection_member(blob, index)), 0)
    return typeface


def load(source: FontSource) -> list[tuple[Any, Path | None, bytes]]:
    """Every face (skia typeface, path, bytes) of a font file or its contents; collections give several."""
    path, blob = _read(source)
    data = skia.Data.MakeWithCopy(blob)
    typefaces = [_typeface(data, blob, index) for index in range(face_count(blob))]
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
def _installed_families() -> tuple[str, ...]:
    """Every installed family name, indexed once on first need."""
    manager = skia.FontMgr.RefDefault()
    return tuple(manager.getFamilyName(index) for index in range(manager.countFamilies()))


def _belongs(typeface: Any, family: str) -> bool:
    """Whether a face's own name table names *family*; some font managers list other families' files under it."""
    return family_names(typeface)[0].lower().startswith(family.lower())


def installed_faces(name: str) -> tuple[str, list[Face]]:
    """The concrete family and its installed faces; generic names pick the first installed candidate.

    The font manager names each style; faces whose name table names another family are dropped.
    """
    manager = skia.FontMgr.RefDefault()
    for family in (*generic_candidates(name), name):
        styles = manager.matchFamily(family)
        if styles.count():
            faces = []
            for index in range(styles.count()):
                typeface, subfamily = styles.createTypeface(index), styles.getStyle(index)[1] or REGULAR_SUBFAMILY
                faces.append(Face.of(family, typeface, describe(typeface, subfamily=subfamily), subfamily=subfamily))
            own = [face for face in faces if _belongs(face.typeface, family)]
            return family, own or faces
    if generic_candidates(name):
        fallback = manager.legacyMakeTypeface("", skia.FontStyle())
        if fallback is not None:
            warnings.warn(f"no installed font for {name!r}; using {fallback.getFamilyName()!r}", stacklevel=3)
            return fallback.getFamilyName(), [Face.of(fallback.getFamilyName(), fallback, describe(fallback))]
    families = {family.lower(): family for family in _installed_families()}
    close = [families[match] for match in difflib.get_close_matches(name.lower(), families, n=SUGGESTIONS)]
    hint = f"; did you mean {' or '.join(repr(match) for match in close)}?" if close else ""
    raise LookupError(f"no installed font family {name!r}{hint} (load files with Typeface.from_files)")
