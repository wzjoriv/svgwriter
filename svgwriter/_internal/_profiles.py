"""
``<color-profile>`` applied on a render copy: ``icc-color(...)`` paints and profiled images become sRGB.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from ._constants import BASE64_SUFFIX, DATA_URI
from ._icc_constants import AUTO_PROFILE, COLOR_PROFILE, ICC_COLOR_RE, ICC_PAINTS, SRGB_PROFILE

if TYPE_CHECKING:
    from ..elements.core import Element

__all__ = ["ProfileRef", "href_bytes", "profile_table", "resolve_profiles"]


class ProfileRef(NamedTuple):
    """A ``<color-profile>``: its ICC bytes (None when unreadable) and rendering intent."""

    data: bytes | None
    intent: str | None


def href_bytes(element: Element, href: str) -> bytes | None:
    """Read the bytes *href* points at, relative to *element*'s base URI.

    Parameters
    ----------
    element : Element
        The element holding the link.
    href : str
        A local path, ``file:`` URL or ``data:`` URI.

    Returns
    -------
    bytes or None
        The contents, or None for remote or unreadable links.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._profiles import href_bytes
    >>> href_bytes(svg.Group(), "data:,abc")
    b'abc'
    """
    import base64
    import binascii
    from pathlib import Path
    from urllib.parse import unquote, unquote_to_bytes, urljoin, urlparse
    from urllib.request import url2pathname

    from ._links import base_uri

    if href.startswith(DATA_URI):
        header, _, payload = href.partition(",")
        try:
            return base64.b64decode(payload) if header.lower().endswith(BASE64_SUFFIX) else unquote_to_bytes(payload)
        except (binascii.Error, ValueError):
            return None
    target = urlparse(urljoin(base_uri(element), href))
    if target.scheme != "file":
        return None
    try:
        return Path(url2pathname(unquote(target.path))).read_bytes()
    except OSError:
        return None


def profile_table(root: Element) -> dict[str, ProfileRef]:
    """The ``<color-profile>`` elements of *root*'s document, by ``name`` and by ``id``.

    Parameters
    ----------
    root : Element
        Any element of the document.

    Returns
    -------
    dict of str to ProfileRef
        Each profile under its name and its ``#id``.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._profiles import profile_table
    >>> doc = svg.Document(10, 10)
    >>> _ = doc.add(svg.ColorProfile("print", "data:,", id="p"))
    >>> sorted(profile_table(doc.root))
    ['#p', 'print']
    """
    table: dict[str, ProfileRef] = {}
    for element in root.root().iter(COLOR_PROFILE):
        href = element.get("xlink:href")
        data = href_bytes(element, str(href)) if href is not None else None
        intent = element.get("rendering-intent")
        ref = ProfileRef(data, None if intent is None else str(intent))
        name, ident = element.get("name"), element.get("id")
        if name is not None:
            table.setdefault(str(name), ref)
        if ident is not None:
            table.setdefault(f"#{ident}", ref)
    return table


def _lookup(table: dict[str, ProfileRef], name: str) -> ProfileRef | None:
    name = name.strip()
    if name.startswith("url(") and name.endswith(")"):
        name = name[len("url("):-1].strip().strip("'\"")
    return table.get(name)


def _converted(text: str, table: dict[str, ProfileRef]) -> str | None:
    from ..color.color import Color
    from ._icc import color_to_srgb, hint_missing, load_profile

    match = ICC_COLOR_RE.match(text)
    if match is None:
        return None
    head, fallback = match.group("head") or "", match.group("color")
    name, *rest = [part.strip() for part in match.group("args").split(",")]
    ref = _lookup(table, name)
    profile = load_profile(ref.data) if ref is not None and ref.data is not None else None
    if ref is not None and profile is None:
        hint_missing()
    try:
        components = [float(part) for part in rest]
    except ValueError:
        components = []
    rgb = color_to_srgb(profile, components, ref.intent if ref else None) if profile and components else None
    if rgb is None:
        return f"{head}{fallback}".strip()
    return f"{head}{Color(*rgb).svg_value()}"


def _profiled_image(image: Element, table: dict[str, ProfileRef]) -> Any:
    from ..attributes.cascade import computed
    from ..elements.structure import Pixels

    setting = str(computed(image, COLOR_PROFILE, AUTO_PROFILE, []) or AUTO_PROFILE).strip()
    href = image.attributes.get("xlink:href")
    if setting.lower() == AUTO_PROFILE or not isinstance(href, str):
        return None
    if setting.lower() == SRGB_PROFILE:
        profile: bytes | str = SRGB_PROFILE
        intent = None
    else:
        ref = _lookup(table, setting)
        if ref is None or ref.data is None:
            return None
        profile, intent = ref.data, ref.intent
    data = href_bytes(image, href)
    if data is None:
        return None
    try:
        return Pixels.decode(data, profile=profile, intent=intent)
    except ValueError:
        return None


def resolve_profiles(root: Element) -> None:
    """Draw colour-managed content in sRGB, in place on a render copy.

    ``icc-color(name, ...)`` in a fill, stroke, stop, flood or lighting colour is converted
    through the named ``<color-profile>``; without that profile, or without the optional
    ``lcms2`` package, its sRGB fallback colour is kept. An ``<image>`` whose
    ``color-profile`` names a profile (or ``sRGB``) is decoded with it.

    Parameters
    ----------
    root : Element
        A render copy with resolved styles.

    Examples
    --------
    >>> import svgwriter as svg
    >>> from svgwriter._internal._profiles import resolve_profiles
    >>> doc = svg.Document(10, 10)
    >>> rect = doc.rect(0, 0, 5, 5, fill="red icc-color(missing, 0.5)")
    >>> resolve_profiles(doc.root)
    >>> str(rect.get("fill"))
    'red'
    """
    from ..elements.structure import Image

    table = profile_table(root)
    for element in root.iter():
        for name in ICC_PAINTS:
            value = element.attributes.get(name)
            if value is None:
                continue
            text = value.svg_value() if hasattr(value, "svg_value") else str(value)
            if "icc-color" in text.lower():
                replaced = _converted(text, table)
                if replaced is not None:
                    element.attributes[name] = replaced
        if isinstance(element, Image):
            pixels = _profiled_image(element, table)
            if pixels is not None:
                element.attributes["xlink:href"] = pixels
